#!/bin/sh
BP_RENTAL_DEVICES="${BP_RENTAL_DEVICES:-$BP_STATE/rental-devices.tsv}"
BP_RENTAL_ENROLL="${BP_RENTAL_ENROLL:-$BP_STATE/rental-enroll.tsv}"
BP_RENTAL_POLICY="${BP_RENTAL_POLICY:-$BP_STATE/rental-policy.tsv}"
BP_RENTAL_INVENTORY="${BP_RENTAL_INVENTORY:-$BP_STATE/rental-inventory.tsv}"
BP_RENTAL_EVENTS="${BP_RENTAL_EVENTS:-$BP_STATE/rental-events.tsv}"
# Volatile heartbeat metadata is NOT paid credit and must never share the
# authoritative rental-devices.tsv row update path.
BP_RENTAL_SEEN_DIR="${BP_RENTAL_SEEN_DIR:-$BP_RUN/rental-last-seen}"

bp_rental_init() {
  bp_init_dirs
  touch "$BP_RENTAL_DEVICES" "$BP_RENTAL_ENROLL" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY" "$BP_RENTAL_EVENTS"
  chmod 600 "$BP_RENTAL_DEVICES" "$BP_RENTAL_ENROLL" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY" "$BP_RENTAL_EVENTS"
  if [ -n "${BP_RENTAL_POLICY_V2:-}" ]; then
    touch "$BP_RENTAL_POLICY_V2"; chmod 600 "$BP_RENTAL_POLICY_V2"
  fi
  [ ! -L "$BP_RENTAL_SEEN_DIR" ] || return 8
  mkdir -p "$BP_RENTAL_SEEN_DIR" || return 8
  chmod 700 "$BP_RENTAL_SEEN_DIR" || return 8
}

bp_rental_clean() { printf '%s' "$1" | tr '\t\r\n' '   '; }
bp_rental_hex() { bp_auth_random_hex "$1"; }

bp_rental_hmac() {
  secret="$1"; data="$2"
  command -v openssl >/dev/null 2>&1 || return 2
  printf '%s' "$data" | openssl dgst -sha256 -hmac "$secret" 2>/dev/null | awk '{print $NF}'
}

bp_rental_enroll_create() {
  label="$(bp_rental_clean "$1")"; ttl="${2:-600}"; now="$(bp_now)"
  case "$ttl" in ''|*[!0-9]*) return 8;; esac
  [ "$ttl" -ge 60 ] 2>/dev/null && [ "$ttl" -le 3600 ] 2>/dev/null || return 8
  id="$(bp_rental_hex 6)" || return 8
  secret="$(bp_rental_hex 18)" || return 8
  printf '%s' "$id" | LC_ALL=C grep -Eq '^[a-f0-9]{12}$' || return 8
  printf '%s' "$secret" | LC_ALL=C grep -Eq '^[a-f0-9]{36}$' || return 8
  [ -f "$BP_RENTAL_ENROLL" ] && [ ! -L "$BP_RENTAL_ENROLL" ] || return 8
  # Reject corrupt or duplicated QR tokens before ever emitting a new one.
  # Full profile also accepts its seven-column redeemed receipt schema.
  if ! awk -F '\t' -v i="$id" '
    { if ((NF!=4 && NF!=7) || length($1)!=12 || $1 !~ /^[a-f0-9]+$/ ||
          length($2)!=36 || $2 !~ /^[a-f0-9]+$/ ||
          $3 !~ /^[0-9]+$/ || ++seen[$1]>1) bad=1 }
    END {if (bad || seen[i]) exit 8}
  ' "$BP_RENTAL_ENROLL" > /dev/null; then
    return 8
  fi
  token="$id.$secret"; expiry=$((now+ttl))
  enroll_tmp="$BP_STATE/.rental-enroll-create.$(bp_tmp_suffix)"
  umask 077
  if ! cat "$BP_RENTAL_ENROLL" > "$enroll_tmp" ||
     ! printf '%s\t%s\t%s\t%s\n' "$id" "$secret" "$expiry" "$label" >> "$enroll_tmp" ||
     ! chmod 600 "$enroll_tmp" ||
     ! mv "$enroll_tmp" "$BP_RENTAL_ENROLL"; then
    rm -f "$enroll_tmp" 2>/dev/null || true
    return 8
  fi
  bp_durable_sync || return 8
  # A failed storage update must never produce a scannable but invalid QR.
  printf '%s\n' "$token"
}

bp_rental_enroll_lookup() {
  awk -F '\t' -v i="$1" '$1==i {print; exit}' "$BP_RENTAL_ENROLL"
}

bp_rental_enroll_mark_redeemed() {
  id="$1"; request_nonce="$2"; did="$3"; dsecret="$4"
  tmp="$BP_STATE/.rental-enroll.$(bp_tmp_suffix)"
  awk -F '\t' -v OFS='\t' -v i="$id" -v n="$request_nonce" -v d="$did" -v s="$dsecret" '
    $1==i {$5=n;$6=d;$7=s}
    {print}
  ' "$BP_RENTAL_ENROLL" > "$tmp" &&
    chmod 600 "$tmp" && mv "$tmp" "$BP_RENTAL_ENROLL"
}

bp_rental_enroll_consume() {
  id="$1"; tmp="$BP_STATE/.rental-enroll.$(bp_tmp_suffix)"
  awk -F '\t' -v i="$id" '$1!=i {print}' "$BP_RENTAL_ENROLL" > "$tmp" &&
    chmod 600 "$tmp" && mv "$tmp" "$BP_RENTAL_ENROLL"
}

bp_rental_enroll_consume_device() {
  did="$1"
  awk -F '\t' -v d="$did" '$6==d {found=1} END{exit found?0:1}' "$BP_RENTAL_ENROLL" || return 3
  tmp="$BP_STATE/.rental-enroll.$(bp_tmp_suffix)"
  awk -F '\t' -v d="$did" '$6!=d {print}' "$BP_RENTAL_ENROLL" > "$tmp" &&
    chmod 600 "$tmp" && mv "$tmp" "$BP_RENTAL_ENROLL"
}

bp_rental_device_line() {
  awk -F '\t' -v d="$1" '$1==d {print; exit}' "$BP_RENTAL_DEVICES"
}

bp_rental_seen_update() {
  seen_id="$1"; seen_time="$2"
  printf '%s\n' "$seen_id" | LC_ALL=C grep -Eq '^[0-9a-f]{24}$' || return 8
  case "$seen_time" in ''|*[!0-9]*) return 8;; esac
  [ -d "$BP_RENTAL_SEEN_DIR" ] && [ ! -L "$BP_RENTAL_SEEN_DIR" ] || return 8
  seen_file="$BP_RENTAL_SEEN_DIR/$seen_id"
  [ ! -L "$seen_file" ] || return 8
  seen_tmp="$BP_RENTAL_SEEN_DIR/.$seen_id.$(bp_tmp_suffix)"
  umask 077
  if ! printf '%s\n' "$seen_time" > "$seen_tmp" ||
     ! chmod 600 "$seen_tmp" ||
     ! mv "$seen_tmp" "$seen_file"; then
    rm -f "$seen_tmp" 2>/dev/null || true
    return 8
  fi
  return 0
}

bp_rental_seen_get() {
  seen_id="$1"; seen_fallback="${2:-0}"
  case "$seen_fallback" in ''|*[!0-9]*) seen_fallback=0;; esac
  printf '%s\n' "$seen_id" | LC_ALL=C grep -Eq '^[0-9a-f]{24}$' ||
    { printf '%s' "$seen_fallback"; return 0; }
  seen_file="$BP_RENTAL_SEEN_DIR/$seen_id"
  if [ -f "$seen_file" ] && [ ! -L "$seen_file" ]; then
    seen_actual="$(cat "$seen_file" 2>/dev/null || true)"
    case "$seen_actual" in ''|*[!0-9]*) ;; *)
      printf '%s' "$seen_actual"; return 0;;
    esac
  fi
  printf '%s' "$seen_fallback"
}

bp_rental_device_write() {
  id="$1"; secret="$2"; lease="$3"; label="$4"; last="$5"
  # This is authoritative paid rental time plus private device identity.
  # Never rename an incomplete/corrupt source snapshot over other leases.
  [ -f "$BP_RENTAL_DEVICES" ] && [ ! -L "$BP_RENTAL_DEVICES" ] || return 8
  printf '%s\n' "$id" | LC_ALL=C grep -Eq '^[A-Za-z0-9_.:-]{2,96}$' || return 8
  case "$lease:$last" in ''|*[!0-9:]*) return 8;; esac
  [ -n "$lease" ] && [ -n "$last" ] && [ -n "$secret" ] || return 8
  for field in "$secret" "$label"; do
    case "$field" in *"$(printf '\t')"*|*"
"*) return 8;; esac
  done
  tmp="$BP_STATE/.rental-devices.$(bp_tmp_suffix)"
  umask 077
  if ! awk -F '\t' -v d="$id" '
    {
      if (NF!=5 || $1 !~ /^[A-Za-z0-9_.:-]+$/ ||
          length($1)>96 || length($2)==0 ||
          $3 !~ /^[0-9]+$/ || $5 !~ /^[0-9]+$/ ||
          ++seen[$1]>1) invalid=1
      if ($1==d) {matches++; next}
      print
    }
    END {if (invalid || matches>1) exit 8}
  ' "$BP_RENTAL_DEVICES" > "$tmp"; then
    rm -f "$tmp" 2>/dev/null || true
    return 8
  fi
  if ! printf '%s\t%s\t%s\t%s\t%s\n' "$id" "$secret" "$lease" "$(bp_rental_clean "$label")" "$last" >> "$tmp"; then
    rm -f "$tmp" 2>/dev/null || true
    return 8
  fi
  if ! chmod 600 "$tmp" || ! mv "$tmp" "$BP_RENTAL_DEVICES"; then
    rm -f "$tmp" 2>/dev/null || true
    return 8
  fi
  bp_durable_sync || return 8
  return 0
}

bp_rental_list_json() {
  first=1; printf '['
  while IFS="$(printf '\t')" read -r id secret lease label last; do
    [ -n "$id" ] || continue
    p="$(bp_rental_policy_line "$id")"
    allowed="$(printf '%s' "$p" | cut -f2)"
    salt="$(printf '%s' "$p" | cut -f3)"
    hash="$(printf '%s' "$p" | cut -f4)"
    preferred="$(printf '%s' "$p" | cut -f6)"
    mode=rental; hidden=""; rev=0; timer_mode=overlay; timer_toggle=1; notifications=1; quick=""
    if command -v bp_rental_policy_v2_get >/dev/null 2>&1; then
      v2="$(bp_rental_policy_v2_get "$id" 2>/dev/null || true)"
      if [ -n "$v2" ]; then
        rev="$(printf '%s' "$v2" | cut -f2)"
        mode="$(printf '%s' "$v2" | cut -f5)"
        allowed="$(printf '%s' "$v2" | cut -f6)"
        hidden="$(printf '%s' "$v2" | cut -f7)"
        preferred="$(printf '%s' "$v2" | cut -f8)"
        timer_mode="$(printf '%s' "$v2" | cut -f9)"
        timer_toggle="$(printf '%s' "$v2" | cut -f10)"
        quick="$(printf '%s' "$v2" | cut -f11)"
        notifications="$(printf '%s' "$v2" | cut -f12)"
        salt="$(printf '%s' "$v2" | cut -f15)"
        hash="$(printf '%s' "$v2" | cut -f16)"
      fi
    fi
    [ "$allowed" = "-" ] && allowed=""
    [ "$hidden" = "-" ] && hidden=""
    [ "$preferred" = "-" ] && preferred=""
    [ "$quick" = "-" ] && quick=""
    # Rental heartbeat is volatile. Never replace a paid lease row to
    # update presence, even when another coin is currently being credited.
    last="$(bp_rental_seen_get "$id" "$last")"
    inventory="$(bp_rental_inventory_get "$id")"
    [ "$salt" != "-" ] && [ -n "$salt" ] && [ "$hash" != "-" ] && [ -n "$hash" ] && admin_set=true || admin_set=false
    [ "$first" = 1 ] || printf ','; first=0
    printf '{"device_id":"%s","label":"%s","lease_until":%s,"last_seen":%s,"policy_revision":%s,"launcher_mode":"%s","allowed_packages":"%s","hidden_packages":"%s","preferred_vendo":"%s","timer_mode":"%s","timer_user_toggle":%s,"quick_controls":"%s","notifications_enabled":%s,"admin_password_set":%s,"inventory":"%s"}' \
      "$(bp_json_escape "$id")" "$(bp_json_escape "$label")" "${lease:-0}" "${last:-0}" "${rev:-0}" "$(bp_json_escape "$mode")" "$(bp_json_escape "$allowed")" "$(bp_json_escape "$hidden")" "$(bp_json_escape "$preferred")" "$(bp_json_escape "$timer_mode")" "${timer_toggle:-1}" "$(bp_json_escape "$quick")" "${notifications:-1}" "$admin_set" "$(bp_json_escape "$inventory")"
  done < "$BP_RENTAL_DEVICES"
  printf ']'
}


bp_rental_policy_line() {
  did="$1"
  line="$(awk -F '\t' -v d="$did" '$1==d {print; exit}' "$BP_RENTAL_POLICY")"
  [ -n "$line" ] && printf '%s\n' "$line" || printf '%s\t*\t-\t-\t4096\t-\n' "$did"
}

bp_rental_policy_ensure() {
  did="$1"
  grep -q "^$did$(printf '\t')" "$BP_RENTAL_POLICY" 2>/dev/null || {
    printf '%s\t*\t-\t-\t4096\t-\n' "$did" >> "$BP_RENTAL_POLICY"
    chmod 600 "$BP_RENTAL_POLICY"
    bp_durable_sync
  }
}

bp_rental_policy_write() {
  did="$1"; allowed="$2"; salt="$3"; hash="$4"; rounds="$5"; preferred="$6"
  tmp="$BP_STATE/.rental-policy.$(bp_tmp_suffix)"
  awk -F '\t' -v d="$did" '$1!=d {print}' "$BP_RENTAL_POLICY" > "$tmp"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$did" "$allowed" "$salt" "$hash" "$rounds" "$preferred" >> "$tmp"
  chmod 600 "$tmp" && mv "$tmp" "$BP_RENTAL_POLICY"
  bp_durable_sync
}

bp_rental_packages_valid() {
  value="$1"
  [ "$value" = "*" ] && return 0
  len="$(printf '%s' "$value" | wc -c)"
  [ "$len" -ge 1 ] && [ "$len" -le 2048 ] || return 1
  printf '%s' "$value" | grep -Eq '^[A-Za-z0-9._,*-]+$'
}

bp_rental_vendo_valid() {
  value="$1"
  [ -z "$value" ] || [ "$value" = "-" ] || printf '%s' "$value" | grep -Eq '^[A-Za-z0-9._-]{1,48}$'
}

bp_rental_policy_set() {
  did="$1"; allowed="$2"; preferred="$3"
  bp_rental_packages_valid "$allowed" || return 2
  bp_rental_vendo_valid "$preferred" || return 2
  line="$(bp_rental_policy_line "$did")"
  salt="$(printf '%s' "$line" | cut -f3)"
  hash="$(printf '%s' "$line" | cut -f4)"
  rounds="$(printf '%s' "$line" | cut -f5)"
  [ -n "$preferred" ] || preferred="-"
  bp_rental_policy_write "$did" "$allowed" "$salt" "$hash" "${rounds:-4096}" "$preferred"
}

bp_rental_admin_password_set() {
  did="$1"; pass="$2"
  [ "$(printf '%s' "$pass" | wc -c)" -ge 8 ] || return 2
  printf '%s' "$pass" | grep -q '[[:cntrl:]]' && return 2
  line="$(bp_rental_policy_line "$did")"
  allowed="$(printf '%s' "$line" | cut -f2)"
  preferred="$(printf '%s' "$line" | cut -f6)"
  salt="$(bp_rental_hex 12)"; rounds=4096
  hash="$(bp_auth_sha256i "$pass" "$salt" "$rounds")" || return 1
  bp_rental_policy_write "$did" "$allowed" "$salt" "$hash" "$rounds" "$preferred"
}

bp_rental_inventory_write() {
  did="$1"; inventory="$2"
  len="$(printf '%s' "$inventory" | wc -c)"
  [ "$len" -le 4096 ] || return 2
  [ -z "$inventory" ] || printf '%s' "$inventory" | grep -Eq '^[A-Za-z0-9._,*-]+$' || return 2
  tmp="$BP_STATE/.rental-inventory.$(bp_tmp_suffix)"
  awk -F '\t' -v d="$did" '$1!=d {print}' "$BP_RENTAL_INVENTORY" > "$tmp"
  [ -n "$inventory" ] || inventory="-"
  printf '%s\t%s\n' "$did" "$inventory" >> "$tmp"
  chmod 600 "$tmp" && mv "$tmp" "$BP_RENTAL_INVENTORY"
}

bp_rental_inventory_get() {
  v="$(awk -F '\t' -v d="$1" '$1==d {print $2; exit}' "$BP_RENTAL_INVENTORY")"
  [ "$v" = "-" ] && v=""
  printf '%s' "$v"
}

bp_rental_event_log() {
  kind="$(bp_rental_clean "$1")"; did="$(bp_rental_clean "$2")"; detail="$(bp_rental_clean "$3")"; now="$(bp_now)"
  event="a:$now:$(bp_tmp_suffix)"
  [ -f "$BP_RENTAL_EVENTS" ] && [ ! -L "$BP_RENTAL_EVENTS" ] || return 8
  # Never mask the audit append failure with the result of chmod/sync.
  printf '%s\t%s\t%s\t%s\t%s\n' "$event" "$did" "$detail" "$now" "$kind" >> "$BP_RENTAL_EVENTS" || return 8
  chmod 600 "$BP_RENTAL_EVENTS" || return 8
  bp_durable_sync || return 8
  return 0
}

bp_rental_device_rename() {
  did="$1"; new_label="$(bp_rental_clean "$2")"
  [ -n "$new_label" ] || return 2
  [ "$(printf '%s' "$new_label" | wc -c)" -le 80 ] || return 2
  line="$(bp_rental_device_line "$did")"; [ -n "$line" ] || return 1
  secret="$(printf '%s' "$line" | cut -f2)"; lease="$(printf '%s' "$line" | cut -f3)"; last="$(printf '%s' "$line" | cut -f5)"
  bp_rental_device_write "$did" "$secret" "$lease" "$new_label" "$last"
  bp_rental_event_log rename "$did" "$new_label"
}

bp_rental_lease_add() {
  did="$1"; seconds="$2"; now="$(bp_now)"
  case "$seconds" in ''|*[!0-9]*) return 2;; esac
  [ "$seconds" -le 2592000 ] 2>/dev/null || return 2
  [ ! -e "$BP_PAID_UNCERTAIN" ] && [ ! -L "$BP_PAID_UNCERTAIN" ] || return 9
  line="$(bp_rental_device_line "$did")"; [ -n "$line" ] || return 1
  secret="$(printf '%s' "$line" | cut -f2)"; lease="$(printf '%s' "$line" | cut -f3)"; label="$(printf '%s' "$line" | cut -f4)"; last="$(printf '%s' "$line" | cut -f5)"
  case "$lease" in ''|*[!0-9]*) return 8;; esac
  base="$lease"; [ "$base" -ge "$now" ] 2>/dev/null || base="$now"
  newlease=$((base+seconds))
  bp_paid_begin || return 9
  if ! bp_rental_device_write "$did" "$secret" "$newlease" "$label" "$last" ||
     ! bp_rental_event_log lease_add "$did" "$seconds"; then
    bp_paid_abort
    return 8
  fi
  bp_paid_commit || return 8
  printf '%s\n' "$newlease"
}

bp_rental_lease_expire() {
  did="$1"; confirm="${2:-}"; now="$(bp_now)"
  [ ! -e "$BP_PAID_UNCERTAIN" ] && [ ! -L "$BP_PAID_UNCERTAIN" ] || return 9
  line="$(bp_rental_device_line "$did")"; [ -n "$line" ] || return 1
  secret="$(printf '%s' "$line" | cut -f2)"; label="$(printf '%s' "$line" | cut -f4)"; last="$(printf '%s' "$line" | cut -f5)"
  lease="$(printf '%s' "$line" | cut -f3)"
  case "$lease" in ''|*[!0-9]*) return 8;; esac
  # Removing still-paid time requires a second, explicit admin operation,
  # never an ordinary expire/close or an accidental stale UI action.
  [ "$lease" -le "$now" ] 2>/dev/null ||
    [ "$confirm" = CONFIRM_FORFEIT ] || return 6
  detail="expired"
  if [ "$lease" -gt "$now" ] 2>/dev/null; then
    detail="confirmed_forfeit_seconds:$((lease-now))"
  fi
  bp_paid_begin || return 9
  if ! bp_rental_device_write "$did" "$secret" "$now" "$label" "$last" ||
     ! bp_rental_event_log expire "$did" "$detail"; then
    bp_paid_abort
    return 8
  fi
  bp_paid_commit || return 8
  printf '%s\n' "$now"
}

bp_rental_device_revoke() {
  did="$1"
  printf '%s\n' "$did" | LC_ALL=C grep -Eq '^[A-Za-z0-9_.:-]{2,96}$' || return 2
  # After a previous interrupted revoke the device record may be missing;
  # refuse subsequent apparent "unknown" results until money is reconciled.
  [ ! -e "$BP_PAID_UNCERTAIN" ] && [ ! -L "$BP_PAID_UNCERTAIN" ] || return 9
  [ -f "$BP_RENTAL_DEVICES" ] && [ ! -L "$BP_RENTAL_DEVICES" ] || return 8
  [ -n "$(bp_rental_device_line "$did")" ] || return 1
  # A corrupt/duplicate paid lease store cannot authorize any deletion.
  if ! awk -F '\t' -v d="$did" '
    NF!=5 || $1 !~ /^[A-Za-z0-9_.:-]+$/ || length($1)>96 ||
      length($2)==0 || $3 !~ /^[0-9]+$/ ||
      $5 !~ /^[0-9]+$/ || ++seen[$1]>1 {bad=1}
    $1==d {found++; lease=$3}
    END {if(bad || found>1)exit 8; if(!found)exit 1}
  ' "$BP_RENTAL_DEVICES"; then
    return 8
  fi
  line="$(bp_rental_device_line "$did")"; [ -n "$line" ] || return 1
  lease="$(printf '%s' "$line" | cut -f3)"
  case "$lease" in ''|*[!0-9]*) return 8;; esac
  # An administrator may expire/settle time via a separate, audited process.
  # Revoke is NEVER consent to silently destroy a paid active rental lease.
  [ "$lease" -le "$(bp_now)" ] 2>/dev/null || return 6
  # Preflight destination paths before the very first mutation, to avoid
  # destructive partial removal when a file is a symlink or special entry.
  for file in "$BP_RENTAL_DEVICES" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY" "${BP_RENTAL_POLICY_V2:-}"; do
    [ -n "$file" ] || continue
    [ ! -e "$file" ] && [ ! -L "$file" ] && continue
    [ -f "$file" ] && [ ! -L "$file" ] || return 8
  done
  for target_file in "$BP_TARGET_DIR"/*.tsv; do
    [ ! -e "$target_file" ] && [ ! -L "$target_file" ] && continue
    [ -f "$target_file" ] && [ ! -L "$target_file" ] || return 8
  done
  # Destructive changes touch several v1 files. Mark uncertainty BEFORE any
  # rename and retain the halt across an interrupted audit or target removal.
  bp_paid_begin || return 9
  for file in "$BP_RENTAL_DEVICES" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY" "${BP_RENTAL_POLICY_V2:-}"; do
    [ -n "$file" ] || continue
    [ -f "$file" ] || continue
    tmp="$BP_STATE/.rental-revoke.$(bp_tmp_suffix)"
    if ! awk -F '\t' -v d="$did" '$1!=d {print}' "$file" > "$tmp" ||
       ! chmod 600 "$tmp" ||
       ! mv "$tmp" "$file"; then
      rm -f "$tmp" 2>/dev/null || true
      bp_paid_abort
      return 8
    fi
  done
  for target_file in "$BP_TARGET_DIR"/*.tsv; do
    [ -f "$target_file" ] || continue
    if [ "$(cut -f1 "$target_file")" = "$did" ]; then
      if ! rm -f "$target_file"; then
        bp_paid_abort
        return 8
      fi
    fi
  done
  if ! bp_rental_event_log revoke "$did" "revoked"; then
    bp_paid_abort
    return 8
  fi
  bp_paid_commit || return 8
  return 0
}

bp_rental_events_json() {
  limit="${1:-64}"
  case "$limit" in ''|*[!0-9]*) limit=64;; esac
  [ "$limit" -ge 1 ] 2>/dev/null || limit=1
  [ "$limit" -le 256 ] 2>/dev/null || limit=256
  first=1; printf '['
  tail -n "$limit" "$BP_RENTAL_EVENTS" 2>/dev/null | while IFS="$(printf '\t')" read -r event did detail when kind; do
    [ -n "$event" ] || continue
    # v0.6.0 development receipts put immutable pulse count in column 5.
    # Hide that internal fingerprint from the original admin kind display.
    case "$kind" in p:*) kind="" ;; esac
    [ -n "$kind" ] || kind="$(printf '%s' "$event" | sed 's/:.*//')"
    [ "$first" = 1 ] || printf ','
    first=0
    printf '{"event":"%s","device_id":"%s","detail":"%s","time":%s,"kind":"%s"}' \
      "$(bp_json_escape "$event")" "$(bp_json_escape "$did")" "$(bp_json_escape "$detail")" "${when:-0}" "$(bp_json_escape "$kind")"
  done
  printf ']'
}

# Keep receipt append independently mockable for fault-injection tests.
bp_rental_append_paid_receipt() {
  # Keep legacy fields 1-4 stable; column 5 binds the signed pulse
  # quantity to this immutable receipt, so altered retries never false-ACK.
  printf '%s\t%s\t%s\t%s\tp:%s\n' "$1" "$2" "$3" "$4" "$5" >> "$BP_RENTAL_EVENTS" || return 8
  chmod 600 "$BP_RENTAL_EVENTS" || return 8
  bp_durable_sync || return 8
}

# P0-0710: use canonical decimal and signed-32-bit safe financial
# arithmetic. A broken lease/receipt must not become an expired/zero lease.
bp_rental_safe_seconds() {
  case "$1" in
    0) ;;
    [1-9]*) case "$1" in *[!0-9]*) return 1;; esac ;;
    *) return 1 ;;
  esac
  [ "$1" -le "$2" ] 2>/dev/null
}

bp_rental_apply_coin() {
  did="$1"; controller="$2"; nonce="$3"; target="$4"; pulses="$5"; now="$(bp_now)"
  # Internal callers must not be able to mint negative/zero/overflowing paid
  # leases even when bypassing the external Vendo CGI parameter checks.
  bp_rental_safe_seconds "$pulses" 20 && [ "$pulses" -ge 1 ] || return 2
  bp_rental_safe_seconds "$now" 2147483647 || return 8
  # Refuse invalid receipt storage before touching a prepaid lease, and never
  # clear an operator-reconcilable uncertainty marker on an ordinary retry.
  [ -f "$BP_RENTAL_EVENTS" ] && [ ! -L "$BP_RENTAL_EVENTS" ] || return 8
  [ ! -e "$BP_STATE/paid-state-uncertain" ] || return 9
  # Read stored paid time BEFORE a duplicate receipt could issue an ACK.
  line="$(bp_rental_device_line "$did")"
  [ -n "$line" ] || return 2
  secret="$(printf '%s' "$line" | cut -f2)"
  lease="$(printf '%s' "$line" | cut -f3)"
  label="$(printf '%s' "$line" | cut -f4)"
  bp_rental_safe_seconds "$lease" 2147483647 || return 8
  event="r:$(printf 'rental|%s|%s|%s' "$controller" "$nonce" "$target" | bp_sha256)"
  # Reject duplicate/corrupt event IDs rather than trusting the first row.
  # Legacy 4-column coin receipts cannot prove the original pulse quantity:
  # refuse an ambiguous ACK, never re-credit or auto-migrate such records.
  old="$(awk -F '\t' -v e="$event" '$1==e {found++; print} END {if(found>1) exit 5}' "$BP_RENTAL_EVENTS")" || return 5
  if [ -n "$old" ]; then
    # RENT-0723: a signed old receipt cannot ACK during another paid writer.
    # Re-read its immutable identity under the shared global paid lock;
    # an optimistic lookup before this lock is never authorization to ACK.
    bp_paid_replay_read_lock || return 9
    old="$(awk -F '\t' -v e="$event" '$1==e {found++; print} END {if(found>1) exit 5}' "$BP_RENTAL_EVENTS")" || {
      bp_paid_replay_read_unlock; return 5;
    }
    [ -n "$old" ] || { bp_paid_replay_read_unlock; return 8; }
    locked_line="$(bp_rental_device_line "$did")"
    [ -n "$locked_line" ] || { bp_paid_replay_read_unlock; return 8; }
    locked_lease="$(printf '%s' "$locked_line" | cut -f3)"
    bp_rental_safe_seconds "$locked_lease" 2147483647 || {
      bp_paid_replay_read_unlock; return 8;
    }
    old_did="$(printf '%s' "$old" | cut -f2)"
    old_lease="$(printf '%s' "$old" | cut -f3)"
    old_pulses="$(printf '%s' "$old" | cut -f5)"
    if [ "$old_did" != "$did" ] || [ "$old_pulses" != "p:$pulses" ] ||
       ! bp_rental_safe_seconds "$old_lease" 2147483647; then
      bp_paid_replay_read_unlock; return 5
    fi
    printf 'duplicate\t%s\n' "$old_lease"
    replay_rc=$?
    bp_paid_replay_read_unlock
    return "$replay_rc"
  fi
  per="$(bp_cfg rental_seconds_per_pulse)"
  [ -n "$per" ] || per=600
  bp_rental_safe_seconds "$per" 86400 && [ "$per" -ge 1 ] || return 8
  base="$lease"
  [ "$base" -gt "$now" ] 2>/dev/null || base="$now"
  delta=$((per * pulses))
  # Reject before signed integer overflow on 32-bit BusyBox/ash targets.
  [ "$base" -le $((2147483647-delta)) ] || return 8
  newlease=$((base + delta))
  # A write-ahead halt marker is persisted before the first money-state write.
  # If a receipt append fails, no success ACK is sent and all subsequent
  # financial mutation must halt for operator reconciliation (not auto-reset).
  bp_paid_begin || return 9
  # RENT-0723: optimistic device/receipt reads were BEFORE the writer lock.
  # Another successful coin payment could have changed paid time meanwhile.
  # Do not overwrite its later lease or record a duplicate receipt with a
  # stale base. No money was changed by this attempt, so bp_paid_commit can
  # safely clear ONLY our newly created pending marker before returning a
  # retryable failure. Any cancellation sync error stays uncertain.
  locked_line="$(bp_rental_device_line "$did")"
  locked_old="$(awk -F '\t' -v e="$event" '$1==e {found++; print} END {if(found>1) exit 5}' "$BP_RENTAL_EVENTS")" || {
    bp_paid_commit || return 8
    return 5
  }
  if [ "$locked_line" != "$line" ] || [ -n "$locked_old" ]; then
    bp_paid_commit || return 8
    return 8
  fi
  if ! bp_rental_device_write "$did" "$secret" "$newlease" "$label" "$now"; then
    bp_paid_abort; return 8
  fi
  if ! bp_rental_append_paid_receipt "$event" "$did" "$newlease" "$now" "$pulses"; then
    bp_paid_abort; return 8
  fi
  bp_paid_commit || return 8
  printf 'credited\t%s\n' "$newlease"
}
