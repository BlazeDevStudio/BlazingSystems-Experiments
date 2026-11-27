#!/bin/sh
# BlazePwifi centralized BlazePisonet SoftTimer member store.
# Source after common.sh and auth.sh.

BP_MEMBERS=${BP_MEMBERS:-$BP_STATE/members.tsv}
BP_MEMBER_EVENTS=${BP_MEMBER_EVENTS:-$BP_STATE/member-events.tsv}
BP_MEMBER_REVISION=${BP_MEMBER_REVISION:-$BP_STATE/member-revision}

bp_member_init() {
  bp_init_dirs
  touch "$BP_MEMBERS" "$BP_MEMBER_EVENTS"
  [ -f "$BP_MEMBER_REVISION" ] || printf '0\n' > "$BP_MEMBER_REVISION"
  chmod 600 "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_MEMBER_REVISION"
}

bp_member_lock() {
  mkdir -p "$BP_RUN"
  exec 7>"$BP_RUN/member.lock"
  flock -w 10 7 || { exec 7>&-; return 1; }
}

bp_member_unlock() {
  flock -u 7 2>/dev/null || true
  exec 7>&-
}

bp_member_norm() {
  printf '%s' "$1" | grep -Eq '^[A-Za-z0-9_.-]{2,32}$' || return 1
  printf '%s' "$1"
}

bp_member_clean() {
  printf '%s' "$1" | tr '\t\r\n' '   ' | cut -c1-96
}

bp_member_global_revision() {
  v="$(cat "$BP_MEMBER_REVISION" 2>/dev/null || echo 0)"
  case "$v" in ''|*[!0-9]*) v=0;; esac
  printf '%s' "$v"
}

bp_member_next_revision() {
  old="$(bp_member_global_revision)"
  next=$((old+1))
  printf '%s\n' "$next" > "$BP_MEMBER_REVISION"
  chmod 600 "$BP_MEMBER_REVISION"
  printf '%s' "$next"
}

bp_member_line() {
  awk -F '\t' -v u="$1" '$1==u {print; exit}' "$BP_MEMBERS"
}

bp_member_event_line() {
  awk -F '\t' -v e="$1" '$1==e {print; exit}' "$BP_MEMBER_EVENTS"
}

bp_member_replay_line() {
  event_id="$1"; controller_id="$2"; username="$3"; kind="$4"
  awk -F '\t' -v e="$event_id" -v s="softtimer:$controller_id" -v u="$username" -v k="$kind"     '$1==e && $3==u && $4==k && $7==s {print; exit}' "$BP_MEMBER_EVENTS"
}

bp_member_hash_password() {
  pass="$1"
  [ "${#pass}" -ge 8 ] || return 2
  command -v bp_auth_random_hex >/dev/null 2>&1 || return 1
  command -v bp_auth_sha256i >/dev/null 2>&1 || return 1
  salt="$(bp_auth_random_hex 12)" || return 1
  rounds="$(bp_cfg member_kdf_rounds 2>/dev/null || true)"
  case "$rounds" in ''|*[!0-9]*) rounds=4096;; esac
  [ "$rounds" -ge 1024 ] 2>/dev/null || rounds=1024
  [ "$rounds" -le 20000 ] 2>/dev/null || rounds=20000
  hash="$(bp_auth_sha256i "$pass" "$salt" "$rounds")"
  printf 'sha256i\t%s\t%s\t%s\n' "$salt" "$hash" "$rounds"
}

bp_member_verify_password() {
  user="$1"; pass="$2"
  line="$(bp_member_line "$user")"; [ -n "$line" ] || return 1
  enabled="$(printf '%s' "$line" | cut -f3)"
  scheme="$(printf '%s' "$line" | cut -f4)"
  salt="$(printf '%s' "$line" | cut -f5)"
  stored="$(printf '%s' "$line" | cut -f6)"
  rounds="$(printf '%s' "$line" | cut -f7)"
  [ "$enabled" = 1 ] || return 1
  case "$scheme" in
    sha256i)
      command -v bp_auth_sha256i >/dev/null 2>&1 || return 1
      got="$(bp_auth_sha256i "$pass" "$salt" "$rounds")"
      ;;
    *) return 1 ;;
  esac
  [ -n "$got" ] && [ "$got" = "$stored" ]
}

# Fields:
# username label enabled scheme salt hash rounds banked_seconds revision updated source
bp_member_write() {
  user="$1"; label="$2"; enabled="$3"; scheme="$4"; salt="$5"; hash="$6"; rounds="$7"; banked="$8"; revision="$9"
  shift 9
  updated="$1"; source="$2"

  tmp="$BP_STATE/.members.$(bp_tmp_suffix)"
  awk -F '\t' -v u="$user" '$1!=u {print}' "$BP_MEMBERS" > "$tmp"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'     "$user" "$(bp_member_clean "$label")" "$enabled" "$scheme" "$salt" "$hash" "$rounds" "$banked" "$revision" "$updated" "$(bp_member_clean "$source")" >> "$tmp"
  chmod 600 "$tmp" && mv "$tmp" "$BP_MEMBERS"
  bp_durable_sync
}

bp_member_create() {
  user="$(bp_member_norm "$1")" || return 2
  label="$(bp_member_clean "$2")"; pass="$3"; source="$(bp_member_clean "$4")"
  [ -z "$(bp_member_line "$user")" ] || return 3
  verifier="$(bp_member_hash_password "$pass")" || return $?
  scheme="$(printf '%s' "$verifier" | cut -f1)"
  salt="$(printf '%s' "$verifier" | cut -f2)"
  hash="$(printf '%s' "$verifier" | cut -f3)"
  rounds="$(printf '%s' "$verifier" | cut -f4)"
  rev="$(bp_member_next_revision)"; now="$(bp_now)"
  bp_member_write "$user" "$label" 1 "$scheme" "$salt" "$hash" "$rounds" 0 "$rev" "$now" "$source"
  bp_member_event_record "admin:$rev:$user" "$now" "$user" create 0 0 "$source" ""
  printf '%s' "$rev"
}

bp_member_patch() {
  user="$(bp_member_norm "$1")" || return 2
  label="$2"; enabled="$3"; source="$(bp_member_clean "$4")"
  line="$(bp_member_line "$user")"; [ -n "$line" ] || return 3
  oldlabel="$(printf '%s' "$line" | cut -f2)"
  oldenabled="$(printf '%s' "$line" | cut -f3)"
  scheme="$(printf '%s' "$line" | cut -f4)"
  salt="$(printf '%s' "$line" | cut -f5)"
  hash="$(printf '%s' "$line" | cut -f6)"
  rounds="$(printf '%s' "$line" | cut -f7)"
  banked="$(printf '%s' "$line" | cut -f8)"
  [ "$label" = "@keep" ] && label="$oldlabel"
  [ "$enabled" = "@keep" ] && enabled="$oldenabled"
  case "$enabled" in 0|1) ;; *) return 2;; esac
  label="$(bp_member_clean "$label")"
  rev="$(bp_member_next_revision)"; now="$(bp_now)"
  bp_member_write "$user" "$label" "$enabled" "$scheme" "$salt" "$hash" "$rounds" "$banked" "$rev" "$now" "$source"
  bp_member_event_record "admin:$rev:$user" "$now" "$user" patch 0 "$banked" "$source" ""
  printf '%s' "$rev"
}

bp_member_set_password() {
  user="$(bp_member_norm "$1")" || return 2
  pass="$2"; source="$(bp_member_clean "$3")"
  line="$(bp_member_line "$user")"; [ -n "$line" ] || return 3
  verifier="$(bp_member_hash_password "$pass")" || return $?
  label="$(printf '%s' "$line" | cut -f2)"
  enabled="$(printf '%s' "$line" | cut -f3)"
  banked="$(printf '%s' "$line" | cut -f8)"
  scheme="$(printf '%s' "$verifier" | cut -f1)"
  salt="$(printf '%s' "$verifier" | cut -f2)"
  hash="$(printf '%s' "$verifier" | cut -f3)"
  rounds="$(printf '%s' "$verifier" | cut -f4)"
  rev="$(bp_member_next_revision)"; now="$(bp_now)"
  bp_member_write "$user" "$label" "$enabled" "$scheme" "$salt" "$hash" "$rounds" "$banked" "$rev" "$now" "$source"
  bp_member_event_record "admin:$rev:$user" "$now" "$user" password_reset 0 "$banked" "$source" ""
  printf '%s' "$rev"
}

bp_member_balance_change() {
  user="$(bp_member_norm "$1")" || return 2
  mode="$2"; seconds="$3"; source="$(bp_member_clean "$4")"; event_id="$5"
  case "$seconds" in ''|*[!0-9]*) return 2;; esac
  [ "$seconds" -le 31536000 ] 2>/dev/null || return 2
  line="$(bp_member_line "$user")"; [ -n "$line" ] || return 3

  if [ -n "$event_id" ]; then
    prior="$(awk -F '\t' -v e="$event_id" -v u="$user" -v k="$mode" -v s="$source" '$1==e && $3==u && $4==k && $7==s {print; exit}' "$BP_MEMBER_EVENTS")"
    if [ -n "$prior" ]; then
      printf '%s\t%s\n' "$(printf '%s' "$prior" | cut -f6)" "$(bp_member_global_revision)"
      return 0
    fi
    [ -z "$(bp_member_event_line "$event_id")" ] || return 5
  fi

  label="$(printf '%s' "$line" | cut -f2)"
  enabled="$(printf '%s' "$line" | cut -f3)"
  scheme="$(printf '%s' "$line" | cut -f4)"
  salt="$(printf '%s' "$line" | cut -f5)"
  hash="$(printf '%s' "$line" | cut -f6)"
  rounds="$(printf '%s' "$line" | cut -f7)"
  banked="$(printf '%s' "$line" | cut -f8)"
  case "$banked" in ''|*[!0-9]*) banked=0;; esac

  case "$mode" in
    add) new=$((banked+seconds)); delta="$seconds"; result="$seconds" ;;
    subtract)
      [ "$banked" -ge "$seconds" ] 2>/dev/null || return 4
      new=$((banked-seconds)); delta="-$seconds"; result="$seconds"
      ;;
    set) new="$seconds"; delta=$((seconds-banked)); result="$seconds" ;;
    restore_all) new=0; delta="-$banked"; result="$banked" ;;
    *) return 2 ;;
  esac

  rev="$(bp_member_next_revision)"; now="$(bp_now)"
  bp_member_write "$user" "$label" "$enabled" "$scheme" "$salt" "$hash" "$rounds" "$new" "$rev" "$now" "$source"
  [ -n "$event_id" ] || event_id="admin:$rev:$user"
  bp_member_event_record "$event_id" "$now" "$user" "$mode" "$delta" "$result" "$source" "$new"
  printf '%s\t%s\n' "$result" "$rev"
}

bp_member_transfer() {
  from="$(bp_member_norm "$1")" || return 2
  to="$(bp_member_norm "$2")" || return 2
  seconds="$3"; source="$(bp_member_clean "$4")"; event_id="$5"
  [ "$from" != "$to" ] || return 2
  case "$seconds" in ''|*[!0-9]*) return 2;; esac
  [ "$seconds" -gt 0 ] 2>/dev/null && [ "$seconds" -le 31536000 ] 2>/dev/null || return 2

  if [ -n "$event_id" ]; then
    prior="$(awk -F '\t' -v e="$event_id" -v u="$from" -v s="$source" '$1==e && $3==u && $4=="transfer" && $7==s {print; exit}' "$BP_MEMBER_EVENTS")"
    if [ -n "$prior" ]; then
      printf '%s\t%s\n' "$(printf '%s' "$prior" | cut -f6)" "$(bp_member_global_revision)"
      return 0
    fi
    [ -z "$(bp_member_event_line "$event_id")" ] || return 5
  fi

  fl="$(bp_member_line "$from")"; tl="$(bp_member_line "$to")"
  [ -n "$fl" ] && [ -n "$tl" ] || return 3

  fbank="$(printf '%s' "$fl" | cut -f8)"; tbank="$(printf '%s' "$tl" | cut -f8)"
  case "$fbank" in ''|*[!0-9]*) fbank=0;; esac
  case "$tbank" in ''|*[!0-9]*) tbank=0;; esac
  [ "$fbank" -ge "$seconds" ] 2>/dev/null || return 4

  rev="$(bp_member_next_revision)"; now="$(bp_now)"
  newf=$((fbank-seconds)); newt=$((tbank+seconds))

  bp_member_write "$from" "$(printf '%s' "$fl" | cut -f2)" "$(printf '%s' "$fl" | cut -f3)" \
    "$(printf '%s' "$fl" | cut -f4)" "$(printf '%s' "$fl" | cut -f5)" "$(printf '%s' "$fl" | cut -f6)" \
    "$(printf '%s' "$fl" | cut -f7)" "$newf" "$rev" "$now" "$source"
  bp_member_write "$to" "$(printf '%s' "$tl" | cut -f2)" "$(printf '%s' "$tl" | cut -f3)" \
    "$(printf '%s' "$tl" | cut -f4)" "$(printf '%s' "$tl" | cut -f5)" "$(printf '%s' "$tl" | cut -f6)" \
    "$(printf '%s' "$tl" | cut -f7)" "$newt" "$rev" "$now" "$source"

  [ -n "$event_id" ] || event_id="admin:$rev:$from>$to"
  bp_member_event_record "$event_id" "$now" "$from" transfer "-$seconds" "$seconds" "$source" "$newf:$to:$newt"
  printf '%s\t%s\n' "$seconds" "$rev"
}

bp_member_delete() {
  user="$(bp_member_norm "$1")" || return 2
  source="$(bp_member_clean "$2")"
  [ -n "$(bp_member_line "$user")" ] || return 3
  rev="$(bp_member_next_revision)"; now="$(bp_now)"
  tmp="$BP_STATE/.members.$(bp_tmp_suffix)"
  awk -F '\t' -v u="$user" '$1!=u {print}' "$BP_MEMBERS" > "$tmp"
  chmod 600 "$tmp" && mv "$tmp" "$BP_MEMBERS"
  bp_member_event_record "admin:$rev:$user" "$now" "$user" delete 0 0 "$source" ""
  bp_durable_sync
  printf '%s' "$rev"
}

# event_id timestamp username kind delta result source detail
bp_member_event_record() {
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'     "$(bp_member_clean "$1")" "$2" "$(bp_member_clean "$3")" "$(bp_member_clean "$4")"     "$5" "$6" "$(bp_member_clean "$7")" "$(bp_member_clean "$8")" >> "$BP_MEMBER_EVENTS"
  chmod 600 "$BP_MEMBER_EVENTS"
  max="$(bp_cfg member_event_history 2>/dev/null || true)"
  case "$max" in ''|*[!0-9]*) max=2048;; esac
  [ "$max" -ge 128 ] 2>/dev/null || max=128
  [ "$max" -le 10000 ] 2>/dev/null || max=10000
  count="$(wc -l < "$BP_MEMBER_EVENTS" 2>/dev/null || echo 0)"
  if [ "$count" -gt "$max" ] 2>/dev/null; then
    tmp="$BP_STATE/.member-events.$(bp_tmp_suffix)"
    tail -n "$max" "$BP_MEMBER_EVENTS" > "$tmp" && chmod 600 "$tmp" && mv "$tmp" "$BP_MEMBER_EVENTS"
  fi
  bp_durable_sync
}

bp_member_public_list_json() {
  first=1; printf '['
  while IFS= read -r line || [ -n "$line" ]; do
    user="$(printf '%s' "$line" | cut -f1)"; [ -n "$user" ] || continue
    label="$(printf '%s' "$line" | cut -f2)"
    enabled="$(printf '%s' "$line" | cut -f3)"
    banked="$(printf '%s' "$line" | cut -f8)"
    revision="$(printf '%s' "$line" | cut -f9)"
    updated="$(printf '%s' "$line" | cut -f10)"
    source="$(printf '%s' "$line" | cut -f11)"
    [ "$first" = 1 ] || printf ','; first=0
    printf '{"username":"%s","label":"%s","enabled":%s,"banked_seconds":%s,"revision":%s,"updated":%s,"source":"%s"}' \
      "$(bp_json_escape "$user")" "$(bp_json_escape "$label")" "${enabled:-0}" "${banked:-0}" "${revision:-0}" "${updated:-0}" "$(bp_json_escape "$source")"
  done < "$BP_MEMBERS"
  printf ']'
}

bp_member_auth_proof_expected() {
  user="$1"; nonce="$2"; controller_id="$3"
  line="$(bp_member_line "$user")"; [ -n "$line" ] || return 1
  enabled="$(printf '%s' "$line" | cut -f3)"
  stored="$(printf '%s' "$line" | cut -f6)"
  [ "$enabled" = 1 ] && [ -n "$stored" ] || return 1
  secret="$(bp_cfg vendo_key)"
  [ -n "$secret" ] || return 1
  printf '%s|%s|%s|%s' "$stored" "$nonce" "$controller_id" "$secret" | bp_sha256
}

bp_member_auth_proof_ok() {
  user="$1"; nonce="$2"; controller_id="$3"; got="$4"
  expected="$(bp_member_auth_proof_expected "$user" "$nonce" "$controller_id")" || return 1
  [ -n "$got" ] && [ "$got" = "$expected" ]
}

bp_member_snapshot_json() {
  first=1; printf '['
  while IFS= read -r line || [ -n "$line" ]; do
    user="$(printf '%s' "$line" | cut -f1)"; [ -n "$user" ] || continue
    label="$(printf '%s' "$line" | cut -f2)"
    enabled="$(printf '%s' "$line" | cut -f3)"
    scheme="$(printf '%s' "$line" | cut -f4)"
    salt="$(printf '%s' "$line" | cut -f5)"
    rounds="$(printf '%s' "$line" | cut -f7)"
    banked="$(printf '%s' "$line" | cut -f8)"
    revision="$(printf '%s' "$line" | cut -f9)"
    updated="$(printf '%s' "$line" | cut -f10)"
    [ "$first" = 1 ] || printf ','; first=0
    printf '{"username":"%s","label":"%s","enabled":%s,"scheme":"%s","salt":"%s","rounds":%s,"banked_seconds":%s,"revision":%s,"updated":%s}' \
      "$(bp_json_escape "$user")" "$(bp_json_escape "$label")" "${enabled:-0}" "$(bp_json_escape "$scheme")" \
      "$(bp_json_escape "$salt")" "${rounds:-0}" "${banked:-0}" "${revision:-0}" "${updated:-0}"
  done < "$BP_MEMBERS"
  printf ']'
}

bp_member_events_json() {
  limit="$1"; user="$2"
  case "$limit" in ''|*[!0-9]*) limit=64;; esac
  [ "$limit" -le 256 ] 2>/dev/null || limit=256
  first=1; printf '['
  if [ -n "$user" ]; then
    lines="$(awk -F '\t' -v u="$user" '$3==u {print}' "$BP_MEMBER_EVENTS" | tail -n "$limit")"
  else
    lines="$(tail -n "$limit" "$BP_MEMBER_EVENTS" 2>/dev/null)"
  fi
  printf '%s\n' "$lines" | while IFS="$(printf '\t')" read -r event ts username kind delta result source detail; do
    [ -n "$event" ] || continue
    [ "$first" = 1 ] || printf ','; first=0
    printf '{"event_id":"%s","timestamp":%s,"username":"%s","kind":"%s","delta_seconds":%s,"result_seconds":%s,"source":"%s","detail":"%s"}'       "$(bp_json_escape "$event")" "${ts:-0}" "$(bp_json_escape "$username")" "$(bp_json_escape "$kind")"       "${delta:-0}" "${result:-0}" "$(bp_json_escape "$source")" "$(bp_json_escape "$detail")"
  done
  printf ']'
}
