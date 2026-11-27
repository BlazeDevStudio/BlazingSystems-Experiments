#!/bin/sh
BP_RENTAL_DEVICES="${BP_RENTAL_DEVICES:-$BP_STATE/rental-devices.tsv}"
BP_RENTAL_ENROLL="${BP_RENTAL_ENROLL:-$BP_STATE/rental-enroll.tsv}"
BP_RENTAL_POLICY="${BP_RENTAL_POLICY:-$BP_STATE/rental-policy.tsv}"
BP_RENTAL_INVENTORY="${BP_RENTAL_INVENTORY:-$BP_STATE/rental-inventory.tsv}"
BP_RENTAL_EVENTS="${BP_RENTAL_EVENTS:-$BP_STATE/rental-events.tsv}"

bp_rental_init() {
  bp_init_dirs
  touch "$BP_RENTAL_DEVICES" "$BP_RENTAL_ENROLL" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY" "$BP_RENTAL_EVENTS"
  chmod 600 "$BP_RENTAL_DEVICES" "$BP_RENTAL_ENROLL" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY" "$BP_RENTAL_EVENTS"
  if [ -n "${BP_RENTAL_POLICY_V2:-}" ]; then
    touch "$BP_RENTAL_POLICY_V2"; chmod 600 "$BP_RENTAL_POLICY_V2"
  fi
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
  case "$ttl" in ''|*[!0-9]*) ttl=600;; esac
  [ "$ttl" -ge 60 ] && [ "$ttl" -le 3600 ] || ttl=600
  id="$(bp_rental_hex 6)"; secret="$(bp_rental_hex 18)"; token="$id.$secret"; expiry=$((now+ttl))
  printf '%s\t%s\t%s\t%s\n' "$id" "$secret" "$expiry" "$label" >> "$BP_RENTAL_ENROLL"
  chmod 600 "$BP_RENTAL_ENROLL"; bp_durable_sync
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

bp_rental_device_write() {
  id="$1"; secret="$2"; lease="$3"; label="$4"; last="$5"
  tmp="$BP_STATE/.rental-devices.$(bp_tmp_suffix)"
  awk -F '\t' -v OFS='\t' -v d="$id" '$1!=d {print}' "$BP_RENTAL_DEVICES" > "$tmp"
  printf '%s\t%s\t%s\t%s\t%s\n' "$id" "$secret" "$lease" "$(bp_rental_clean "$label")" "$last" >> "$tmp"
  chmod 600 "$tmp" && mv "$tmp" "$BP_RENTAL_DEVICES"; bp_durable_sync
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
  for file in "$BP_RENTAL_DEVICES" "$BP_RENTAL_POLICY" "$BP_RENTAL_INVENTORY" "${BP_RENTAL_POLICY_V2:-}"; do
    [ -n "$file" ] || continue
    [ -f "$file" ] || continue
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
  event="r:$(printf 'rental|%s|%s|%s' "$controller" "$nonce" "$target" | bp_sha256)"
  old="$(awk -F '\t' -v e="$event" '$1==e {print; exit}' "$BP_RENTAL_EVENTS")"
  if [ -n "$old" ]; then
    printf 'duplicate\t%s\n' "$(printf '%s' "$old" | cut -f3)"
    return 0
  fi
  line="$(bp_rental_device_line "$did")"
  [ -n "$line" ] || return 2
  secret="$(printf '%s' "$line" | cut -f2)"
  lease="$(printf '%s' "$line" | cut -f3)"
  label="$(printf '%s' "$line" | cut -f4)"
  per="$(bp_cfg rental_seconds_per_pulse)"
  [ -n "$per" ] || per=600
  case "$per" in ''|*[!0-9]*) per=600;; esac
  [ "$per" -ge 1 ] 2>/dev/null && [ "$per" -le 86400 ] 2>/dev/null || per=600
  base="$lease"
  [ "$base" -gt "$now" ] 2>/dev/null || base="$now"
  newlease=$((base + per * pulses))
  bp_rental_device_write "$did" "$secret" "$newlease" "$label" "$now"
  printf '%s\t%s\t%s\t%s\n' "$event" "$did" "$newlease" "$now" >> "$BP_RENTAL_EVENTS"
  chmod 600 "$BP_RENTAL_EVENTS"
  bp_durable_sync
  printf 'credited\t%s\n' "$newlease"
}
