#!/bin/sh
BP_RENTAL_DEVICES="${BP_RENTAL_DEVICES:-$BP_STATE/rental-devices.tsv}"
BP_RENTAL_ENROLL="${BP_RENTAL_ENROLL:-$BP_STATE/rental-enroll.tsv}"
BP_RENTAL_POLICY="${BP_RENTAL_POLICY:-$BP_STATE/rental-policy.tsv}"
BP_RENTAL_INVENTORY="${BP_RENTAL_INVENTORY:-$BP_STATE/rental-inventory.tsv}"
BP_RENTAL_EVENTS="${BP_RENTAL_EVENTS:-$BP_STATE/rental-events.tsv}"
# Ephemeral presence metadata must never overwrite a paid rental lease row.
BP_RENTAL_SEEN_DIR="${BP_RENTAL_SEEN_DIR:-$BP_RUN/rental-last-seen}"

bp_rental_init() {
  bp_init_dirs
  touch "$BP_RENTAL_DEVICES" "$BP_RENTAL_ENROLL" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY" "$BP_RENTAL_EVENTS"
  chmod 600 "$BP_RENTAL_DEVICES" "$BP_RENTAL_ENROLL" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY" "$BP_RENTAL_EVENTS"
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
    { if (NF!=4 || length($1)!=12 || $1 !~ /^[a-f0-9]+$/ ||
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

bp_rental_enroll_consume() {
  enroll_id="$1"
  printf '%s' "$enroll_id" | LC_ALL=C grep -Eq '^[0-9a-f]{12}$' || return 8
  [ -f "$BP_RENTAL_ENROLL" ] && [ ! -L "$BP_RENTAL_ENROLL" ] || return 8
  enroll_tmp="$BP_STATE/.rental-enroll.$(bp_tmp_suffix)"
  umask 077
  # Do not confirm a one-time token was spent if it was missing, duplicated
  # or the enrollment registry was already malformed. Preserve old bytes.
  if ! awk -F '\t' -v i="$enroll_id" '
    {
      if (NF!=4 || length($1)!=12 || $1 !~ /^[a-f0-9]+$/ ||
          length($2)!=36 || $2 !~ /^[a-f0-9]+$/ ||
          $3 !~ /^[0-9]+$/ || ++seen[$1]>1) invalid=1
      if ($1==i) {removed++; next}
      print
    }
    END {if (invalid || removed!=1) exit 8}
  ' "$BP_RENTAL_ENROLL" > "$enroll_tmp" ||
     ! chmod 600 "$enroll_tmp" ||
     ! mv "$enroll_tmp" "$BP_RENTAL_ENROLL"; then
    rm -f "$enroll_tmp" 2>/dev/null || true
    return 8
  fi
  bp_durable_sync || return 8
  return 0
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
    [ "$preferred" = "-" ] && preferred=""
    # Presence is volatile; last_seen does not belong in a paid lease rewrite.
    last="$(bp_rental_seen_get "$id" "$last")"
    inventory="$(bp_rental_inventory_get "$id")"
    [ "$salt" != "-" ] && [ "$hash" != "-" ] && admin_set=true || admin_set=false
    [ "$first" = 1 ] || printf ','; first=0
    printf '{"device_id":"%s","label":"%s","lease_until":%s,"last_seen":%s,"allowed_packages":"%s","preferred_vendo":"%s","admin_password_set":%s,"inventory":"%s"}' \
      "$(bp_json_escape "$id")" "$(bp_json_escape "$label")" "${lease:-0}" "${last:-0}" "$(bp_json_escape "$allowed")" "$(bp_json_escape "$preferred")" "$admin_set" "$(bp_json_escape "$inventory")"
  done < "$BP_RENTAL_DEVICES"
  printf ']'
}


bp_rental_policy_line() {
  did="$1"
  line="$(awk -F '\t' -v d="$did" '$1==d {print; exit}' "$BP_RENTAL_POLICY")"
  [ -n "$line" ] && printf '%s\n' "$line" || printf '%s\t*\t-\t-\t4096\t-\n' "$did"
}

bp_rental_policy_ensure() {
  policy_did="$1"
  printf '%s' "$policy_did" | LC_ALL=C grep -Eq '^[0-9a-f]{24}$' || return 8
  [ -f "$BP_RENTAL_POLICY" ] && [ ! -L "$BP_RENTAL_POLICY" ] || return 8
  policy_tmp="$BP_STATE/.rental-policy.$(bp_tmp_suffix)"
  umask 077
  # Check every source row and duplicate ID before copying a replacement.
  # Existing policies must be preserved; never append a truncated record.
  if ! awk -F '\t' -v d="$policy_did" '
    {
      if (NF!=6 || length($1)!=24 || $1 !~ /^[a-f0-9]+$/ ||
          ++seen[$1]>1) invalid=1
      if ($1==d) found++
      print
    }
    END {
      if (invalid || found>1) exit 8
      if (!found) print d,"*","-","-","4096","-"
    }
  ' OFS="$(printf '\t')" "$BP_RENTAL_POLICY" > "$policy_tmp" ||
     ! chmod 600 "$policy_tmp" ||
     ! mv "$policy_tmp" "$BP_RENTAL_POLICY"; then
    rm -f "$policy_tmp" 2>/dev/null || true
    return 8
  fi
  bp_durable_sync || return 8
  return 0
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
  printf '%s\t%s\t%s\t%s\t%s\n' "$event" "$did" "$detail" "$now" "$kind" >> "$BP_RENTAL_EVENTS"
  chmod 600 "$BP_RENTAL_EVENTS"
  bp_durable_sync
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
  line="$(bp_rental_device_line "$did")"; [ -n "$line" ] || return 1
  secret="$(printf '%s' "$line" | cut -f2)"; lease="$(printf '%s' "$line" | cut -f3)"; label="$(printf '%s' "$line" | cut -f4)"; last="$(printf '%s' "$line" | cut -f5)"
  base="$lease"; [ "$base" -ge "$now" ] 2>/dev/null || base="$now"
  newlease=$((base+seconds))
  bp_rental_device_write "$did" "$secret" "$newlease" "$label" "$last"
  bp_rental_event_log lease_add "$did" "$seconds"
  printf '%s\n' "$newlease"
}

bp_rental_lease_expire() {
  did="$1"; now="$(bp_now)"
  line="$(bp_rental_device_line "$did")"; [ -n "$line" ] || return 1
  secret="$(printf '%s' "$line" | cut -f2)"; label="$(printf '%s' "$line" | cut -f4)"; last="$(printf '%s' "$line" | cut -f5)"
  bp_rental_device_write "$did" "$secret" "$now" "$label" "$last"
  bp_rental_event_log expire "$did" "0"
  printf '%s\n' "$now"
}

bp_rental_device_revoke() {
  did="$1"; [ -n "$(bp_rental_device_line "$did")" ] || return 1
  for file in "$BP_RENTAL_DEVICES" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY"; do
    tmp="$BP_STATE/.rental-revoke.$(bp_tmp_suffix)"
    awk -F '\t' -v d="$did" '$1!=d {print}' "$file" > "$tmp" || return 1
    chmod 600 "$tmp" && mv "$tmp" "$file" || return 1
  done
  for target_file in "$BP_TARGET_DIR"/*.tsv; do
    [ -f "$target_file" ] || continue
    [ "$(cut -f1 "$target_file")" = "$did" ] && rm -f "$target_file"
  done
  bp_rental_event_log revoke "$did" "revoked"
  bp_durable_sync
}

bp_rental_events_json() {
  limit="${1:-64}"
  case "$limit" in ''|*[!0-9]*) limit=64;; esac
  [ "$limit" -ge 1 ] 2>/dev/null || limit=1
  [ "$limit" -le 256 ] 2>/dev/null || limit=256
  first=1; printf '['
  tail -n "$limit" "$BP_RENTAL_EVENTS" 2>/dev/null | while IFS="$(printf '\t')" read -r event did detail when kind; do
    [ -n "$event" ] || continue
    [ -n "$kind" ] || kind="$(printf '%s' "$event" | sed 's/:.*//')"
    [ "$first" = 1 ] || printf ','
    first=0
    printf '{"event":"%s","device_id":"%s","detail":"%s","time":%s,"kind":"%s"}' \
      "$(bp_json_escape "$event")" "$(bp_json_escape "$did")" "$(bp_json_escape "$detail")" "${when:-0}" "$(bp_json_escape "$kind")"
  done
  printf ']'
}

bp_rental_apply_coin() {
  did="$1"; controller="$2"; nonce="$3"; target="$4"; pulses="$5"; now="$(bp_now)"
  # Called only under the Vendo CGI's global accounting lock. No ACK,
  # including an old duplicate, while a previous paid write is disputed.
  [ ! -e "$BP_PAID_UNCERTAIN" ] && [ ! -L "$BP_PAID_UNCERTAIN" ] || return 9
  case "$pulses" in ''|*[!0-9]*) return 2;; esac
  [ "$pulses" -ge 1 ] 2>/dev/null && [ "$pulses" -le 20 ] 2>/dev/null || return 2
  [ -f "$BP_RENTAL_EVENTS" ] && [ ! -L "$BP_RENTAL_EVENTS" ] || return 8
  event="r:$(printf 'rental|%s|%s|%s' "$controller" "$nonce" "$target" | bp_sha256)"
  old="$(awk -F '\t' -v e="$event" '$1==e {print; exit}' "$BP_RENTAL_EVENTS")" || return 8
  if [ -n "$old" ]; then
    old_did="$(printf '%s' "$old" | cut -f2)"
    old_lease="$(printf '%s' "$old" | cut -f3)"
    old_kind="$(printf '%s' "$old" | cut -f5)"
    # Legacy four-field receipts lack the original pulse quantity and
    # cannot prove an exact replay. Do not falsely ACK a changed amount.
    [ "$old_did" = "$did" ] && [ "$old_kind" = "coin:$pulses" ] ||
      return 9
    case "$old_lease" in ''|*[!0-9]*) return 9;; esac
    printf 'duplicate\t%s\n' "$old_lease"
    return 0
  fi
  line="$(bp_rental_device_line "$did")"
  [ -n "$line" ] || return 2
  secret="$(printf '%s' "$line" | cut -f2)"
  lease="$(printf '%s' "$line" | cut -f3)"
  label="$(printf '%s' "$line" | cut -f4)"
  last="$(printf '%s' "$line" | cut -f5)"
  case "$lease:$last" in ''|*[!0-9:]*) return 8;; esac
  per="$(bp_cfg rental_seconds_per_pulse)"
  [ -n "$per" ] || per=600
  case "$per" in ''|*[!0-9]*) per=600;; esac
  [ "$per" -ge 1 ] 2>/dev/null && [ "$per" -le 86400 ] 2>/dev/null || per=600
  base="$lease"
  [ "$base" -gt "$now" ] 2>/dev/null || base="$now"
  newlease=$((base + per * pulses))
  # Both paid lease and receipt are still separate legacy TSV writes. A
  # persisted uncertain marker prevents unsafe retry on either failure.
  bp_paid_begin || return 9
  if ! bp_rental_device_write "$did" "$secret" "$newlease" "$label" "$last"; then
    bp_paid_abort
    return 8
  fi
  if ! printf '%s\t%s\t%s\t%s\tcoin:%s\n' "$event" "$did" "$newlease" "$now" "$pulses" >> "$BP_RENTAL_EVENTS" ||
     ! chmod 600 "$BP_RENTAL_EVENTS" ||
     ! bp_durable_sync; then
    bp_paid_abort
    return 8
  fi
  bp_paid_commit || return 8
  printf 'credited\t%s\n' "$newlease"
}
