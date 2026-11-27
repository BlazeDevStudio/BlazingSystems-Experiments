#!/bin/sh
BP_CONTROLLERS="$BP_STATE/controllers.tsv"

bp_controller_init() {
  bp_init_dirs
  touch "$BP_CONTROLLERS"
  chmod 600 "$BP_CONTROLLERS"
}

bp_controller_line() {
  awk -F '\t' -v d="$1" '$1==d {print; exit}' "$BP_CONTROLLERS"
}

bp_controller_ensure() {
  id="$1"
  bp_controller_init
  grep -q "^$id$(printf '\t')" "$BP_CONTROLLERS" 2>/dev/null || {
    printf '%s\t1\t1\t1\t1\t-1\t-1\t-1\t1\t1\t1\t40\t400\t6\t1\n' "$id" >> "$BP_CONTROLLERS"
    chmod 600 "$BP_CONTROLLERS"
    bp_durable_sync
  }
}

bp_controller_bool() {
  case "$1" in 0|1) return 0;; *) return 1;; esac
}

bp_controller_pin() {
  [ "$1" = -1 ] && return 0
  case "$1" in ''|*[!0-9]*) return 1;; esac
  [ "$1" -le 63 ]
}

bp_controller_uint() {
  value="$1"; min="$2"; max="$3"
  case "$value" in ''|*[!0-9]*) return 1;; esac
  [ "$value" -ge "$min" ] && [ "$value" -le "$max" ]
}

bp_controller_write() {
  id="$1"; shift
  tmp="$BP_STATE/.controllers.$(bp_tmp_suffix)"
  awk -F '\t' -v d="$id" '$1!=d {print}' "$BP_CONTROLLERS" > "$tmp"
  printf '%s' "$id" >> "$tmp"
  for value in "$@"; do printf '\t%s' "$value" >> "$tmp"; done
  printf '\n' >> "$tmp"
  chmod 600 "$tmp" && mv "$tmp" "$BP_CONTROLLERS"
  bp_durable_sync
}

bp_controller_set() {
  id="$1"; enabled="$2"; coin="$3"; relay="$4"; led="$5"; cpin="$6"; rpin="$7"; lpin="$8"; clow="$9"
  shift 9
  rhigh="$1"; lhigh="$2"; debounce="$3"; group="$4"; retries="$5"
  for value in "$enabled" "$coin" "$relay" "$led" "$clow" "$rhigh" "$lhigh"; do bp_controller_bool "$value" || return 2; done
  for value in "$cpin" "$rpin" "$lpin"; do bp_controller_pin "$value" || return 2; done
  bp_controller_uint "$debounce" 1 2000 || return 2
  bp_controller_uint "$group" 10 10000 || return 2
  bp_controller_uint "$retries" 1 60 || return 2
  line="$(bp_controller_line "$id")"
  rev="$(printf '%s' "$line" | cut -f15)"
  [ -n "$rev" ] || rev=0
  rev=$((rev+1))
  bp_controller_write "$id" "$enabled" "$coin" "$relay" "$led" "$cpin" "$rpin" "$lpin" "$clow" "$rhigh" "$lhigh" "$debounce" "$group" "$retries" "$rev"
}

bp_controller_json() {
  id="$1"
  bp_controller_ensure "$id"
  line="$(bp_controller_line "$id")"
  enabled="$(printf '%s' "$line" | cut -f2)"
  coin="$(printf '%s' "$line" | cut -f3)"
  relay="$(printf '%s' "$line" | cut -f4)"
  led="$(printf '%s' "$line" | cut -f5)"
  cpin="$(printf '%s' "$line" | cut -f6)"
  rpin="$(printf '%s' "$line" | cut -f7)"
  lpin="$(printf '%s' "$line" | cut -f8)"
  clow="$(printf '%s' "$line" | cut -f9)"
  rhigh="$(printf '%s' "$line" | cut -f10)"
  lhigh="$(printf '%s' "$line" | cut -f11)"
  debounce="$(printf '%s' "$line" | cut -f12)"
  group="$(printf '%s' "$line" | cut -f13)"
  retries="$(printf '%s' "$line" | cut -f14)"
  rev="$(printf '%s' "$line" | cut -f15)"
  printf '{"enabled":%s,"coin_enabled":%s,"relay_enabled":%s,"led_enabled":%s,"coin_pin":%s,"relay_pin":%s,"led_pin":%s,"coin_active_low":%s,"relay_active_high":%s,"led_active_high":%s,"coin_debounce_ms":%s,"pulse_group_ms":%s,"max_wifi_retries":%s,"config_revision":%s}' "$enabled" "$coin" "$relay" "$led" "$cpin" "$rpin" "$lpin" "$clow" "$rhigh" "$lhigh" "$debounce" "$group" "$retries" "$rev"
}

bp_controller_list_json() {
  bp_controller_init
  first=1
  printf '['
  while IFS="$(printf '\t')" read -r id enabled coin relay led cpin rpin lpin clow rhigh lhigh debounce group retries rev; do
    [ -n "$id" ] || continue
    seen="$(awk -F '\t' -v d="$id" '$1==d {print $2; exit}' "$BP_VENDOS")"
    ip="$(awk -F '\t' -v d="$id" '$1==d {print $3; exit}' "$BP_VENDOS")"
    [ -n "$seen" ] || seen=0
    [ "$first" = 1 ] || printf ','
    first=0
    printf '{"id":"%s","last_seen":%s,"ip":"%s","enabled":%s,"coin_enabled":%s,"relay_enabled":%s,"led_enabled":%s,"coin_pin":%s,"relay_pin":%s,"led_pin":%s,"coin_active_low":%s,"relay_active_high":%s,"led_active_high":%s,"coin_debounce_ms":%s,"pulse_group_ms":%s,"max_wifi_retries":%s,"config_revision":%s}' "$(bp_json_escape "$id")" "$seen" "$(bp_json_escape "$ip")" "$enabled" "$coin" "$relay" "$led" "$cpin" "$rpin" "$lpin" "$clow" "$rhigh" "$lhigh" "$debounce" "$group" "$retries" "$rev"
  done < "$BP_CONTROLLERS"
  printf ']'
}
