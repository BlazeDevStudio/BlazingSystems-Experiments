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


# PHX-L-CORE P0 #31: shared controller-paid admission linearization.
# fd4 is distinct from paid fd6, member fd7, auth fd8, account fd9.
# Callers must acquire this only AFTER any member/account writer lock,
# and hold through the durable paid commit. Controller admin holds it
# through its config write. Previously committed receipts are checked first.
bp_controller_admission_lock() {
  mkdir -p "$BP_RUN" || return 8
  exec 4>"$BP_RUN/controller-admission.lock" || return 8
  flock -w 10 4 || { exec 4>&-; return 8; }
}
bp_controller_admission_unlock() {
  flock -u 4 2>/dev/null || true
  exec 4>&-
}
bp_controller_paid_allowed() {
  controller_id="$1"; operation="$2"
  [ -f "$BP_CONTROLLERS" ] && [ ! -L "$BP_CONTROLLERS" ] || return 1
  # Reject absent, duplicated or malformed controller rows; do not
  # silently create/re-enable a controller at the financial decision.
  awk -F '\t' -v d="$controller_id" -v op="$operation" '
    # A paid admission needs the complete legacy 15-column registry row,
    # not just three forged enabled fields. Match existing setter bounds.
    function flag(v) { return v=="0" || v=="1" }
    function uint(v, lo, hi) {
      return v ~ /^[0-9]+$/ && v+0 >= lo && v+0 <= hi
    }
    function pin(v) { return v=="-1" || uint(v,0,63) }
    function valid() {
      return NF==15 && flag($2) && flag($3) && flag($4) && flag($5) &&
        pin($6) && pin($7) && pin($8) && flag($9) && flag($10) && flag($11) &&
        uint($12,1,2000) && uint($13,10,10000) && uint($14,1,60) &&
        $15 ~ /^[0-9]+$/ && $15+0 >= 1
    }
    $1==d {
      n++
      if (!valid()) malformed=1
      enabled=$2
      coin_enabled=$3
    }
    END {
      if (n!=1 || malformed || enabled!="1" ||
          (op=="coin" && coin_enabled!="1")) exit 1
    }
  ' "$BP_CONTROLLERS"
}

bp_controller_write() {
  id="$1"; shift
  tmp="$BP_STATE/.controllers.$(bp_tmp_suffix)"
  # A failed copy or partial append must never replace the prior
  # controller registry: it also carries enabled/coin-enabled admission.
  if ! awk -F '\t' -v d="$id" '$1!=d {print}' "$BP_CONTROLLERS" > "$tmp"; then
    rm -f "$tmp" 2>/dev/null || true
    return 8
  fi
  if ! printf '%s' "$id" >> "$tmp"; then
    rm -f "$tmp" 2>/dev/null || true
    return 8
  fi
  for value in "$@"; do
    if ! printf '\t%s' "$value" >> "$tmp"; then
      rm -f "$tmp" 2>/dev/null || true
      return 8
    fi
  done
  if ! printf '\n' >> "$tmp"; then
    rm -f "$tmp" 2>/dev/null || true
    return 8
  fi
  chmod 600 "$tmp" && mv "$tmp" "$BP_CONTROLLERS" || {
    rm -f "$tmp" 2>/dev/null || true
    return 8
  }
  bp_durable_sync || return 8
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
  bp_controller_admission_lock || return 8
  line="$(bp_controller_line "$id")"
  rev="$(printf '%s' "$line" | cut -f15)"
  [ -n "$rev" ] || rev=0
  rev=$((rev+1))
  if bp_controller_write "$id" "$enabled" "$coin" "$relay" "$led" "$cpin" "$rpin" "$lpin" "$clow" "$rhigh" "$lhigh" "$debounce" "$group" "$retries" "$rev"; then
    bp_controller_admission_unlock
    return 0
  fi
  bp_controller_admission_unlock
  return 8
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
