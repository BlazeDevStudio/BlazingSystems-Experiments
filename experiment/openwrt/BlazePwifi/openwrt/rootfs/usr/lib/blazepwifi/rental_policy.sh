#!/bin/sh
BP_RENTAL_POLICY_V2="${BP_RENTAL_POLICY_V2:-$BP_STATE/rental-policy-v2.tsv}"

bp_rental_policy_v2_init() {
  touch "$BP_RENTAL_POLICY_V2"
  chmod 600 "$BP_RENTAL_POLICY_V2"
}

bp_rental_policy_v2_line() {
  awk -F '\t' -v d="$1" '$1==d {print; exit}' "$BP_RENTAL_POLICY_V2"
}

bp_rental_policy_v2_valid_mode() {
  [ "$1" = rental ] || [ "$1" = unrestricted ]
}

bp_rental_policy_v2_bool() {
  [ "$1" = 0 ] || [ "$1" = 1 ]
}

bp_rental_policy_v2_list_valid() {
  value="$1"; max="${2:-2048}"
  [ "$(printf '%s' "$value" | wc -c)" -le "$max" ] || return 1
  [ -z "$value" ] || printf '%s' "$value" | grep -Eq '^[A-Za-z0-9._,*-]+$'
}

bp_rental_policy_migrate() {
  did="$1"
  bp_rental_policy_v2_init
  [ -n "$(bp_rental_policy_v2_line "$did")" ] && return 0
  old="$(bp_rental_policy_line "$did")"
  allowed="$(printf '%s' "$old" | cut -f2)"
  salt="$(printf '%s' "$old" | cut -f3)"
  hash="$(printf '%s' "$old" | cut -f4)"
  rounds="$(printf '%s' "$old" | cut -f5)"
  preferred="$(printf '%s' "$old" | cut -f6)"
  [ -n "$allowed" ] || allowed="*"
  [ -n "$salt" ] || salt="-"
  [ -n "$hash" ] || hash="-"
  [ -n "$rounds" ] || rounds=4096
  [ -n "$preferred" ] || preferred="-"
  now="$(bp_now)"
  tmp="$BP_STATE/.rental-policy-v2.$(bp_tmp_suffix)"
  awk -F '\t' -v d="$did" '$1!=d {print}' "$BP_RENTAL_POLICY_V2" > "$tmp" || return 1
  printf '%s\t1\t%s\tmigration\trental\t%s\t-\t%s\toverlay\t1\tvolume_down,volume_up,floating_timer,network_status,battery_status,bluetooth_status,flashlight\t1\thold\t4000\t%s\t%s\t%s\t0\t-\n'     "$did" "$now" "$allowed" "$preferred" "$salt" "$hash" "$rounds" >> "$tmp" || return 1
  chmod 600 "$tmp" && mv "$tmp" "$BP_RENTAL_POLICY_V2" || return 1
  bp_durable_sync
}

bp_rental_policy_v2_get() {
  did="$1"
  bp_rental_policy_migrate "$did" || return 1
  bp_rental_policy_v2_line "$did"
}

bp_rental_policy_v2_json() {
  line="$(bp_rental_policy_v2_get "$1")" || return 1
  IFS="$(printf '\t')" read -r did rev updated by mode allowed hidden preferred timer_mode timer_toggle quick notifications gesture_type gesture_value salt hash rounds grace caps <<EOF
$line
EOF
  [ "$allowed" = "-" ] && allowed=""
  [ "$hidden" = "-" ] && hidden=""
  [ "$preferred" = "-" ] && preferred=""
  [ "$quick" = "-" ] && quick=""
  [ "$caps" = "-" ] && caps=""
  printf '{"device_id":"%s","policy_revision":%s,"updated_at":%s,"updated_by":"%s","launcher_mode":"%s","allowed_packages":"%s","hidden_packages":"%s","preferred_vendo":"%s","timer_mode":"%s","timer_user_toggle":%s,"quick_controls":"%s","notifications_enabled":%s,"admin_gesture_type":"%s","admin_gesture_value":"%s","offline_grace":%s,"capabilities":"%s"}'     "$(bp_json_escape "$did")" "${rev:-1}" "${updated:-0}" "$(bp_json_escape "$by")"     "$(bp_json_escape "$mode")" "$(bp_json_escape "$allowed")" "$(bp_json_escape "$hidden")"     "$(bp_json_escape "$preferred")" "$(bp_json_escape "$timer_mode")" "${timer_toggle:-1}"     "$(bp_json_escape "$quick")" "${notifications:-1}" "$(bp_json_escape "$gesture_type")"     "$(bp_json_escape "$gesture_value")" "${grace:-0}" "$(bp_json_escape "$caps")"
}

bp_rental_policy_v2_patch() {
  did="$1"; expected="$2"; actor="$3"; mode_new="$4"; allowed_new="$5"; hidden_new="$6"; preferred_new="$7"
  timer_toggle_new="$8"; notifications_new="$9"; shift 9
  quick_new="$1"; gesture_new="$2"; admin_password="$3"; timer_mode_new="${4:-@keep}"

  case "$expected" in ''|*[!0-9]*) return 3;; esac
  line="$(bp_rental_policy_v2_get "$did")" || return 1
  IFS="$(printf '\t')" read -r id rev updated by mode allowed hidden preferred timer_mode timer_toggle quick notifications gesture_type gesture_value salt hash rounds grace caps <<EOF
$line
EOF
  [ "$expected" = "$rev" ] || return 4

  [ "$mode_new" = "@keep" ] || mode="$mode_new"
  [ "$allowed_new" = "@keep" ] || allowed="$allowed_new"
  [ "$hidden_new" = "@keep" ] || { hidden="$hidden_new"; [ -n "$hidden" ] || hidden="-"; }
  [ "$preferred_new" = "@keep" ] || { preferred="$preferred_new"; [ -n "$preferred" ] || preferred="-"; }
  [ "$timer_mode_new" = "@keep" ] || timer_mode="$timer_mode_new"
  [ "$timer_toggle_new" = "@keep" ] || timer_toggle="$timer_toggle_new"
  [ "$notifications_new" = "@keep" ] || notifications="$notifications_new"
  [ "$quick_new" = "@keep" ] || { quick="$quick_new"; [ -n "$quick" ] || quick="-"; }
  [ "$gesture_new" = "@keep" ] || gesture_value="$gesture_new"

  bp_rental_policy_v2_valid_mode "$mode" || return 2
  bp_rental_packages_valid "$allowed" || return 2
  [ "$hidden" = "-" ] || bp_rental_policy_v2_list_valid "$hidden" 2048 || return 2
  bp_rental_vendo_valid "$preferred" || return 2
  case "$timer_mode" in overlay|always|off) ;; *) return 2;; esac
  bp_rental_policy_v2_bool "$timer_toggle" || return 2
  bp_rental_policy_v2_bool "$notifications" || return 2
  [ "$quick" = "-" ] || bp_rental_policy_v2_list_valid "$quick" 1024 || return 2
  printf '%s' "$gesture_value" | grep -Eq '^[0-9]{4,5}$' || return 2
  [ "$gesture_value" -ge 1500 ] 2>/dev/null && [ "$gesture_value" -le 15000 ] 2>/dev/null || return 2

  if [ -n "$admin_password" ] && [ "$admin_password" != "@keep" ]; then
    [ "$(printf '%s' "$admin_password" | wc -c)" -ge 8 ] || return 2
    printf '%s' "$admin_password" | grep -q '[[:cntrl:]]' && return 2
    salt="$(bp_rental_hex 12)"; rounds=4096
    hash="$(bp_auth_sha256i "$admin_password" "$salt" "$rounds")" || return 1
  fi

  newrev=$((rev+1)); now="$(bp_now)"
  actor="$(bp_rental_clean "$actor")"; [ -n "$actor" ] || actor=device
  tmp="$BP_STATE/.rental-policy-v2.$(bp_tmp_suffix)"
  awk -F '\t' -v d="$did" '$1!=d {print}' "$BP_RENTAL_POLICY_V2" > "$tmp" || return 1
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'     "$did" "$newrev" "$now" "$actor" "$mode" "$allowed" "$hidden" "$preferred" "$timer_mode"     "$timer_toggle" "$quick" "$notifications" "$gesture_type" "$gesture_value" "$salt" "$hash"     "$rounds" "$grace" "$caps" >> "$tmp" || return 1
  chmod 600 "$tmp" && mv "$tmp" "$BP_RENTAL_POLICY_V2" || return 1

  # Keep the v0.3 compatibility row synchronized.
  bp_rental_policy_write "$did" "$allowed" "$salt" "$hash" "$rounds" "$preferred" || return 1
  bp_rental_event_log policy_patch "$did" "revision=$newrev actor=$actor"
  printf '%s\n' "$newrev"
}
