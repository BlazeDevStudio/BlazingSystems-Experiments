#!/bin/sh
# BlazePwifi centralized BlazePisonet SoftTimer member store.
# Source after common.sh and auth.sh.

BP_MEMBERS=${BP_MEMBERS:-$BP_STATE/members.tsv}
BP_MEMBER_EVENTS=${BP_MEMBER_EVENTS:-$BP_STATE/member-events.tsv}
BP_MEMBER_REVISION=${BP_MEMBER_REVISION:-$BP_STATE/member-revision}

bp_member_init() {
  bp_init_dirs || return 8
  # PAY-0729: a missing global revision with existing member/receipt data
  # may be an interrupted write or restore. Never silently reset it to 0.
  [ ! -L "$BP_MEMBERS" ] && [ ! -L "$BP_MEMBER_EVENTS" ] &&
    [ ! -L "$BP_MEMBER_REVISION" ] || return 8
  if [ ! -f "$BP_MEMBER_REVISION" ]; then
    [ ! -s "$BP_MEMBERS" ] && [ ! -s "$BP_MEMBER_EVENTS" ] || return 8
    printf '0\n' > "$BP_MEMBER_REVISION" || return 8
  fi
  touch "$BP_MEMBERS" "$BP_MEMBER_EVENTS" || return 8
  chmod 600 "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_MEMBER_REVISION" || return 8
}

bp_member_lock() {
  mkdir -p "$BP_RUN"
  exec 7>"$BP_RUN/member.lock"
  flock -w 10 7 || { exec 7>&-; return 1; }
  # A prior uncertain paid mutation requires explicit reconciliation.
  [ ! -e "$BP_STATE/paid-state-uncertain" ] || { bp_member_unlock; return 9; }
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

# PAY-0729: revision 0 is only legitimate for a genuinely fresh store.
# Malformed/missing revision and member rows ahead of the global revision
# require reconciliation, NOT replacement by a plausible zero.
bp_member_revision_strict() {
  [ -f "$BP_MEMBER_REVISION" ] && [ ! -L "$BP_MEMBER_REVISION" ] &&
    [ -f "$BP_MEMBERS" ] && [ ! -L "$BP_MEMBERS" ] || return 8
  old="$(cat "$BP_MEMBER_REVISION" 2>/dev/null)" || return 8
  bp_member_safe_seconds "$old" 2147483646 || return 8
  # Detect a lost/reset global revision against existing member revisions.
  # This is a v1 consistency guard, not an independent antirollback witness.
  awk -F '\t' -v revision="$old" '
    NF!=11 || $9 !~ /^(0|[1-9][0-9]*)$/ ||
    length($9)>10 || $9+0>revision {bad=1}
    {if(++seen[$1]>1) bad=1}
    END {if(bad) exit 8}
  ' "$BP_MEMBERS" || return 8
  printf '%s' "$old"
}

# PAY-0737: a signed controller snapshot is financial authority input.
# The caller MUST hold the global paid replay lock while validating and
# serializing it, even though this helper itself never mutates balances.
# Refuse malformed/duplicate rows and invalid/missing money data rather than
# signing invented zero values. This does not prove independent freshness.
bp_member_signed_read_integrity() {
  bp_member_revision_strict >/dev/null || return 8
  # PAY-0742: Vendo member_snapshot/member_auth sign a public financial
  # read model. Do not sign plausible balances when ANY paid receipt (even
  # unrelated) is corrupt/duplicated or the global cutover is quarantined.
  # Caller holds the PAY-0711 global financial read lock.
  bp_member_financial_receipt_capacity_ok || return 8
  awk -F '\t' '
    NF!=11 || $1 !~ /^[A-Za-z0-9_.-]+$/ ||
    $3 !~ /^(0|1)$/ || $7 !~ /^[0-9]+$/ ||
    $8 !~ /^(0|[1-9][0-9]*)$/ ||
    length($8)>10 || $8+0>2147483647 ||
    $10 !~ /^[0-9]+$/ {bad=1}
    END {if(bad) exit 8}
  ' "$BP_MEMBERS" || return 8
  return 0
}

bp_member_next_revision() {
  old="$(bp_member_revision_strict)" || return 8
  next=$((old+1))
  printf '%s\n' "$next" > "$BP_MEMBER_REVISION" || return 8
  chmod 600 "$BP_MEMBER_REVISION" || return 8
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

  # Member rows are paid-state material. Never replace them if copying
  # existing members or appending the new record failed. Also refuse an
  # existing malformed/duplicated record rather than truncating balances.
  [ -f "$BP_MEMBERS" ] && [ ! -L "$BP_MEMBERS" ] || return 8
  case "$banked:$revision" in *[!0-9:]*|'') return 8;; esac
  tmp="$BP_STATE/.members.$(bp_tmp_suffix)"
  umask 077
  if ! awk -F '\t' -v u="$user" '
    NF!=11 || $1 !~ /^[A-Za-z0-9_.-]+$/ ||
      $8 !~ /^[0-9]+$/ {bad=1}
    $1==u {same++; next}
    {print}
    END {if (bad || same>1) exit 7}
  ' "$BP_MEMBERS" > "$tmp"; then
    rm -f "$tmp" 2>/dev/null || true
    return 8
  fi
  if ! printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$user" "$(bp_member_clean "$label")" "$enabled" "$scheme" "$salt" "$hash" "$rounds" "$banked" "$revision" "$updated" "$(bp_member_clean "$source")" >> "$tmp"; then
    rm -f "$tmp" 2>/dev/null || true
    return 8
  fi
  if ! chmod 600 "$tmp" || ! mv "$tmp" "$BP_MEMBERS"; then
    rm -f "$tmp" 2>/dev/null || true
    return 8
  fi
  bp_durable_sync || return 8
  return 0
}

bp_member_create() {
  # Mixing v1 admin mutations with a lab v2 authority would fork paid state.
  [ "${BP_MEMBER_V2_LAB:-0}" != 1 ] || return 9
  user="$(bp_member_norm "$1")" || return 2
  label="$(bp_member_clean "$2")"; pass="$3"; source="$(bp_member_clean "$4")"
  [ -z "$(bp_member_line "$user")" ] || return 3
  verifier="$(bp_member_hash_password "$pass")" || return $?
  scheme="$(printf '%s' "$verifier" | cut -f1)"
  salt="$(printf '%s' "$verifier" | cut -f2)"
  hash="$(printf '%s' "$verifier" | cut -f3)"
  rounds="$(printf '%s' "$verifier" | cut -f4)"
  bp_paid_begin || return 9
  rev="$(bp_member_next_revision)" || { bp_paid_abort; return 8; }
  now="$(bp_now)"
  if ! bp_member_write "$user" "$label" 1 "$scheme" "$salt" "$hash" "$rounds" 0 "$rev" "$now" "$source" ||
     ! bp_member_event_record "admin:$rev:$user" "$now" "$user" create 0 0 "$source" ""; then
    bp_paid_abort; return 8
  fi
  bp_paid_commit || return 8
  printf '%s' "$rev"
}

bp_member_patch() {
  # Mixing v1 admin mutations with a lab v2 authority would fork paid state.
  [ "${BP_MEMBER_V2_LAB:-0}" != 1 ] || return 9
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
  bp_paid_begin || return 9
  rev="$(bp_member_next_revision)" || { bp_paid_abort; return 8; }
  now="$(bp_now)"
  if ! bp_member_write "$user" "$label" "$enabled" "$scheme" "$salt" "$hash" "$rounds" "$banked" "$rev" "$now" "$source" ||
     ! bp_member_event_record "admin:$rev:$user" "$now" "$user" patch 0 "$banked" "$source" ""; then
    bp_paid_abort; return 8
  fi
  bp_paid_commit || return 8
  printf '%s' "$rev"
}

bp_member_set_password() {
  # Mixing v1 admin mutations with a lab v2 authority would fork paid state.
  [ "${BP_MEMBER_V2_LAB:-0}" != 1 ] || return 9
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
  bp_paid_begin || return 9
  rev="$(bp_member_next_revision)" || { bp_paid_abort; return 8; }
  now="$(bp_now)"
  if ! bp_member_write "$user" "$label" "$enabled" "$scheme" "$salt" "$hash" "$rounds" "$banked" "$rev" "$now" "$source" ||
     ! bp_member_event_record "admin:$rev:$user" "$now" "$user" password_reset 0 "$banked" "$source" ""; then
    bp_paid_abort; return 8
  fi
  bp_paid_commit || return 8
  printf '%s' "$rev"
}

# PAY-0712: validate a previously recorded paid receipt and its current
# read-model before the Vendo signed-replay shortcut can acknowledge it.
# Run only under PAY-0711's paid financial replay lock. This is read-only;
# it does NOT reconstruct money from a receipt or certify v1 crash atomicity.
bp_member_replay_snapshot_ok() (
  event_id="$1"; expected_user="$2"; expected_kind="$3"
  expected_source="$4"; expected_seconds="$5"; expected_to="${6:-}"
  # PAY-0742: real signed Vendo member_bank, member_restore and
  # member_transfer replay their ORIGINAL paid receipt directly through
  # this function, bypassing the direct member_balance_change path. A valid
  # current event must not ACK while some OTHER paid event is malformed.
  # Scan the entire bounded corpus under the existing financial read lock.
  bp_member_financial_receipt_capacity_ok || exit 1
  [ -f "$BP_MEMBER_EVENTS" ] && [ ! -L "$BP_MEMBER_EVENTS" ] || exit 1
  [ -f "$BP_MEMBERS" ] && [ ! -L "$BP_MEMBERS" ] || exit 1
  [ -f "$BP_MEMBER_REVISION" ] && [ ! -L "$BP_MEMBER_REVISION" ] || exit 1
  revision="$(cat "$BP_MEMBER_REVISION" 2>/dev/null)" || exit 1
  bp_member_safe_seconds "$revision" 2147483647 || exit 1
  receipt="$(awk -F '\t' -v e="$event_id" '
    $1==e {n++; if(NF!=8) bad=1; record=$0}
    END {if(n!=1 || bad) exit 1; print record}
  ' "$BP_MEMBER_EVENTS")" || exit 1
  [ -n "$receipt" ] || exit 1
  user="$(printf '%s' "$receipt" | cut -f3)"
  kind="$(printf '%s' "$receipt" | cut -f4)"
  delta="$(printf '%s' "$receipt" | cut -f5)"
  result="$(printf '%s' "$receipt" | cut -f6)"
  source="$(printf '%s' "$receipt" | cut -f7)"
  detail="$(printf '%s' "$receipt" | cut -f8)"
  [ "$user" = "$expected_user" ] && [ "$kind" = "$expected_kind" ] &&
    [ "$source" = "$expected_source" ] || exit 1
  bp_member_safe_seconds "$result" 2147483647 || exit 1
  # Validate every member row, including uniqueness. One corrupt member
  # elsewhere means the v1 read-model cannot substantiate a paid ACK.
  if ! awk -F '\t' -v want="$expected_user" -v dest="$expected_to" '
    NF!=11 || ($1 !~ /^[A-Za-z0-9_.-]+$/ || length($1)<2 || length($1)>32) ||
      $3 !~ /^(0|1)$/ || $7 !~ /^[0-9]+$/ ||
      $8 !~ /^(0|[1-9][0-9]*)$/ ||
      $9 !~ /^(0|[1-9][0-9]*)$/ ||
      $10 !~ /^(0|[1-9][0-9]*)$/ {bad=1}
    {if (++seen[$1] > 1) bad=1; if($1==want) from++; if($1==dest) to++;
      if($9+0 > maxrev) maxrev=$9+0;
      if(length($8)>10 || $8+0>2147483647 ||
         length($9)>10 || $9+0>2147483647) bad=1}
    END {if(bad || from!=1 || (dest!="" && to!=1)) exit 1}
  ' "$BP_MEMBERS"; then
    exit 1
  fi
  # Do not silently turn missing/garbled revision metadata into revision 0.
  max_revision="$(awk -F '\t' 'BEGIN {v=0} $9+0>v {v=$9+0} END {printf "%.0f",v}' "$BP_MEMBERS")" || exit 1
  [ "$max_revision" -le "$revision" ] 2>/dev/null || exit 1
  case "$kind" in
    add)
      bp_member_safe_seconds "$expected_seconds" 31536000 || exit 1
      [ "$result" = "$expected_seconds" ] &&
        [ "$delta" = "$expected_seconds" ] || exit 1
      ;;
    restore_all)
      [ "$expected_seconds" = 0 ] && [ "$delta" = "-$result" ] &&
        [ "$detail" = 0 ] || exit 1
      ;;
    transfer)
      bp_member_safe_seconds "$expected_seconds" 31536000 || exit 1
      [ "$result" = "$expected_seconds" ] &&
        [ "$delta" = "-$expected_seconds" ] || exit 1
      prior_to="$(printf '%s' "$detail" | awk -F: 'NF==3 {print $2}')"
      [ "$prior_to" = "$expected_to" ] || exit 1
      from_after="$(printf '%s' "$detail" | cut -d: -f1)"
      to_after="$(printf '%s' "$detail" | cut -d: -f3)"
      bp_member_safe_seconds "$from_after" 2147483647 &&
        bp_member_safe_seconds "$to_after" 2147483647 || exit 1
      ;;
    *) exit 1 ;;
  esac
  exit 0
)

# Paid receipts cannot be retained in a rolling display-history window:
# doing so re-accepts an old, previously successful controller event ID.
# This cap is a fail-closed bridge for legacy random v1 event IDs, NOT a
# substitute for an authenticated v2 sequence journal or lost-ACK recovery.
bp_member_financial_receipt_capacity_ok() {
  # PAY-0730: no direct member replay ACK or fresh credit may bypass a
  # pending v2 authority cutover, even outside the signed Vendo CGI lock.
  bp_paid_v2_cutover_pending && return 1
  # This executes before any v1 replay ACK as well as fresh money writes.
  # A corrupt revision cannot be acknowledged as a successful old event.
  bp_member_revision_strict >/dev/null || return 1
  [ ! -e "$BP_STATE/paid-state-uncertain" ] || return 1
  [ -f "$BP_MEMBER_EVENTS" ] && [ ! -L "$BP_MEMBER_EVENTS" ] || return 1
  case "$BP_MEMBER_EVENTS" in /dev/*) return 1;; esac
  bytes="$(wc -c < "$BP_MEMBER_EVENTS" 2>/dev/null)" || return 1
  case "$bytes" in ''|*[!0-9]*) return 1;; esac
  # Keep headroom for an appended record and a future defensive snapshot.
  [ "$bytes" -le 4190208 ] 2>/dev/null || return 1
  # PAY-0740: a correct-ID receipt lookup is not enough. Corruption or
  # duplicate IDs elsewhere in this authoritative v1 replay corpus may hide
  # previously paid events and allow them to be credited again. Refuse ALL
  # new/replayed money before touching a balance; bounded scan, no trimming.
  LC_ALL=C awk -F '\t' '
    NF!=8 || $1=="" || ++seen[$1]>1 {bad=1}
    $4=="add" || $4=="subtract" || $4=="set" ||
    $4=="restore_all" || $4=="transfer" {
      if ($2 !~ /^[0-9]+$/ || $3=="" || $5 !~ /^-?[0-9]+$/ ||
          $6 !~ /^[0-9]+$/ || $7=="") bad=1
    }
    END {if (bad) exit 8}
  ' "$BP_MEMBER_EVENTS" || return 1
  return 0
}

bp_member_financial_kind() {
  case "$1" in add|subtract|set|restore_all|transfer) return 0;; esac
  return 1
}

# P0-0710: money fields MUST be canonical base-10 integers within signed
# 32-bit arithmetic bounds on all supported POSIX shell targets. Refuse an
# invalid persisted balance; NEVER substitute zero or silently octal-parse.
bp_member_safe_seconds() {
  case "$1" in
    0) ;;
    [1-9]*) case "$1" in *[!0-9]*) return 1;; esac ;;
    *) return 1 ;;
  esac
  [ "$1" -le "$2" ] 2>/dev/null
}

# PAY-0713: actual member money entrypoints can use the v2 atomic authority
# ONLY in a private, marker-gated synthetic /tmp laboratory fixture. The
# production/v1 path stays unchanged and migration remains disabled.
bp_member_v2_lab_load() {
  [ "${BP_MEMBER_V2_LAB:-0}" = 1 ] || return 9
  case "$BP_STATE" in /tmp/blaze-v2-member-*/state) ;; *) return 9;; esac
  root="${BP_STATE%/state}"
  tail="${root#/tmp/blaze-v2-member-}"
  case "$tail" in ''|*/*|*..*|*[!A-Za-z0-9]*) return 9;; esac
  [ "$BP_RUN" = "$root/run" ] &&
    [ "$BP_MEMBERS" = "$BP_STATE/members.tsv" ] &&
    [ "$BP_MEMBER_EVENTS" = "$BP_STATE/member-events.tsv" ] &&
    [ "$BP_MEMBER_REVISION" = "$BP_STATE/member-revision" ] || return 9
  [ -d "$root" ] && [ ! -L "$root" ] &&
    [ -f "$root/.blaze-v2-member-synthetic-only" ] &&
    [ ! -L "$root/.blaze-v2-member-synthetic-only" ] || return 9
  [ "$(cat "$root/.blaze-v2-member-synthetic-only" 2>/dev/null)" = 'BLAZE-V2-MEMBER-SYNTHETIC-ONLY' ] || return 9
  # PAY-0714: Synthetic authority code is NOT shipped inside rootfs. An
  # explicit absolute, regular test helper is mandatory; missing or relative
  # paths reject before any source evaluation or paid read-model writes.
  lab_helper="${BP_MEMBER_V2_LAB_HELPER:-}"
  [ -n "$lab_helper" ] || return 9
  case "$lab_helper" in /*) ;; *) return 9;; esac
  [ -f "$lab_helper" ] && [ ! -L "$lab_helper" ] || return 9
  . "$lab_helper" || return 9
}

bp_member_balance_change() {
  if [ "${BP_MEMBER_V2_LAB:-0}" = 1 ]; then
    bp_member_v2_lab_load || return 9
    bp_member_v2_lab_dispatch balance "$@" ; return $?
  fi
  user="$(bp_member_norm "$1")" || return 2
  mode="$2"; seconds="$3"; source="$(bp_member_clean "$4")"; event_id="$5"
  bp_member_safe_seconds "$seconds" 31536000 || return 2
  line="$(bp_member_line "$user")"; [ -n "$line" ] || return 3
  banked="$(printf '%s' "$line" | cut -f8)"
  bp_member_safe_seconds "$banked" 2147483647 || return 8
  # Do not accept paid credits if the legacy receipt file cannot retain IDs.
  bp_member_financial_receipt_capacity_ok || return 7

  if [ -n "$event_id" ]; then
    prior="$(awk -F '\t' -v e="$event_id" -v u="$user" -v k="$mode" -v s="$source" '$1==e && $3==u && $4==k && $7==s {print; exit}' "$BP_MEMBER_EVENTS")"
    if [ -n "$prior" ]; then
      prior_seconds="$(printf '%s' "$prior" | cut -f6)"
      bp_member_safe_seconds "$prior_seconds" 2147483647 || return 5
      # Reusing an old ID with a different amount is NOT a successful
      # replay: it is a payload collision and must not ACK the new intent.
      case "$mode" in
        add|subtract|set)
          [ "$prior_seconds" -eq "$seconds" ] 2>/dev/null || return 5 ;;
      esac
      printf '%s\t%s\n' "$prior_seconds" "$(bp_member_global_revision)"
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
  case "$mode" in
    add)
      # Check before addition; arithmetic may wrap on 32-bit OpenWrt.
      [ "$banked" -le $((2147483647-seconds)) ] || return 8
      new=$((banked+seconds)); delta="$seconds"; result="$seconds"
      ;;
    subtract)
      [ "$banked" -ge "$seconds" ] 2>/dev/null || return 4
      new=$((banked-seconds)); delta="-$seconds"; result="$seconds"
      ;;
    set) new="$seconds"; delta=$((seconds-banked)); result="$seconds" ;;
    restore_all) new=0; delta="-$banked"; result="$banked" ;;
    *) return 2 ;;
  esac

  # A durable quarantine marker precedes the balance change. If receipt
  # append or filesystem synchronization fails, leave it set and refuse ACK.
  # This protects retries by halting payments; real crash-atomic v2 WAL is
  # still required before public release.
  bp_paid_begin || return 9
  rev="$(bp_member_next_revision)" || { bp_paid_abort; return 8; }
  now="$(bp_now)"
  if ! bp_member_write "$user" "$label" "$enabled" "$scheme" "$salt" "$hash" "$rounds" "$new" "$rev" "$now" "$source"; then
    bp_paid_abort; return 8
  fi
  [ -n "$event_id" ] || event_id="admin:$rev:$user"
  if ! bp_member_event_record "$event_id" "$now" "$user" "$mode" "$delta" "$result" "$source" "$new"; then
    bp_paid_abort; return 8
  fi
  bp_paid_commit || return 8
  printf '%s\t%s\n' "$result" "$rev"
}

bp_member_transfer() {
  if [ "${BP_MEMBER_V2_LAB:-0}" = 1 ]; then
    bp_member_v2_lab_load || return 9
    bp_member_v2_lab_dispatch transfer "$@" ; return $?
  fi
  from="$(bp_member_norm "$1")" || return 2
  to="$(bp_member_norm "$2")" || return 2
  seconds="$3"; source="$(bp_member_clean "$4")"; event_id="$5"
  [ "$from" != "$to" ] || return 2
  bp_member_safe_seconds "$seconds" 31536000 && [ "$seconds" -gt 0 ] || return 2
  bp_member_financial_receipt_capacity_ok || return 7
  # Validate the source immediately. Defer destination existence until
  # AFTER receipt-collision detection: a reused signed event for a different
  # recipient is a collision (rc=5), even if that recipient does not exist.
  # No correct duplicate can ACK until BOTH stored balances are valid.
  fl="$(bp_member_line "$from")"; tl="$(bp_member_line "$to")"
  [ -n "$fl" ] || return 3
  fbank="$(printf '%s' "$fl" | cut -f8)"
  bp_member_safe_seconds "$fbank" 2147483647 || return 8

  if [ -n "$event_id" ]; then
    prior="$(awk -F '\t' -v e="$event_id" -v u="$from" -v s="$source" '$1==e && $3==u && $4=="transfer" && $7==s {print; exit}' "$BP_MEMBER_EVENTS")"
    if [ -n "$prior" ]; then
      prior_seconds="$(printf '%s' "$prior" | cut -f6)"
      bp_member_safe_seconds "$prior_seconds" 2147483647 || return 5
      prior_detail="$(printf '%s' "$prior" | cut -f8)"
      # Transfer receipt detail is from_balance:destination:to_balance.
      # Missing/mismatched destination metadata is ambiguous: fail closed.
      prior_destination="$(printf '%s' "$prior_detail" | awk -F: 'NF==3 {print $2}')"
      [ "$prior_seconds" -eq "$seconds" ] 2>/dev/null &&
        [ "$prior_destination" = "$to" ] || return 5
      # A matching receipt must not ACK an absent or corrupt destination.
      [ -n "$tl" ] || return 3
      tbank="$(printf '%s' "$tl" | cut -f8)"
      bp_member_safe_seconds "$tbank" 2147483647 || return 8
      printf '%s\t%s\n' "$prior_seconds" "$(bp_member_global_revision)"
      return 0
    fi
    [ -z "$(bp_member_event_line "$event_id")" ] || return 5
  fi

  [ -n "$tl" ] || return 3
  tbank="$(printf '%s' "$tl" | cut -f8)"
  bp_member_safe_seconds "$tbank" 2147483647 || return 8
  [ "$fbank" -ge "$seconds" ] 2>/dev/null || return 4
  # Prevent destination overflow on signed 32-bit shells before subtraction.
  [ "$tbank" -le $((2147483647-seconds)) ] || return 8

  bp_paid_begin || return 9
  rev="$(bp_member_next_revision)" || { bp_paid_abort; return 8; }
  now="$(bp_now)"
  newf=$((fbank-seconds)); newt=$((tbank+seconds))

  # A transfer must never expose a half-debited member file. Build both
  # modified rows in a private snapshot, then replace members.tsv in one rename.
  # The caller holds bp_member_lock; a separate transaction journal remains
  # necessary to make the event receipt and retry semantics crash-atomic.
  tmp="$BP_STATE/.member-transfer.$(bp_tmp_suffix)"
  if ! awk -F '\t' -v OFS='\t' -v f="$from" -v t="$to" \
      -v fb="$newf" -v tb="$newt" -v r="$rev" -v ts="$now" -v src="$source" '
      $1==f { $8=fb; $9=r; $10=ts; $11=src; fc++ }
      $1==t { $8=tb; $9=r; $10=ts; $11=src; tc++ }
      { print }
      END { if (fc!=1 || tc!=1) exit 4 }
    ' "$BP_MEMBERS" > "$tmp"; then
    rm -f "$tmp"; bp_paid_abort; return 8
  fi
  if ! chmod 600 "$tmp" || ! mv "$tmp" "$BP_MEMBERS"; then
    rm -f "$tmp"; bp_paid_abort; return 8
  fi
  if ! bp_durable_sync; then bp_paid_abort; return 8; fi

  [ -n "$event_id" ] || event_id="admin:$rev:$from>$to"
  if ! bp_member_event_record "$event_id" "$now" "$from" transfer "-$seconds" "$seconds" "$source" "$newf:$to:$newt"; then
    bp_paid_abort; return 8
  fi
  bp_paid_commit || return 8
  printf '%s\t%s\n' "$seconds" "$rev"
}

bp_member_delete() {
  # Mixing v1 admin mutations with a lab v2 authority would fork paid state.
  [ "${BP_MEMBER_V2_LAB:-0}" != 1 ] || return 9
  user="$(bp_member_norm "$1")" || return 2
  source="$(bp_member_clean "$2")"
  # The member row may have been replaced before an event/EIO interruption.
  # Returning "unknown member" on replay would hide the disputed deletion.
  [ ! -e "$BP_PAID_UNCERTAIN" ] && [ ! -L "$BP_PAID_UNCERTAIN" ] || return 9
  line="$(bp_member_line "$user")"
  [ -n "$line" ] || return 3
  banked="$(printf '%s\n' "$line" | cut -f8)"
  # This is an account record containing PURCHASED TIME, not a cosmetic
  # contact. A deletion must never silently destroy a positive balance.
  case "$banked" in ''|*[!0-9]*) return 7;; esac
  [ "$banked" -eq 0 ] 2>/dev/null || return 6
  # Build and commit deletion+event under the paid-state quarantine.
  # This is conservative v1 containment, NOT a v2 crash-atomic journal.
  bp_paid_begin || return 9
  rev="$(bp_member_next_revision)" || { bp_paid_abort; return 8; }
  now="$(bp_now)"
  tmp="$BP_STATE/.members.$(bp_tmp_suffix)"
  if ! awk -F '\t' -v u="$user" '
    $1==u {deleted++; next}
    {print}
    END {if (deleted!=1) exit 1}
  ' "$BP_MEMBERS" > "$tmp" ||
     ! chmod 600 "$tmp" ||
     ! mv "$tmp" "$BP_MEMBERS"; then
    rm -f "$tmp" 2>/dev/null || true
    bp_paid_abort
    return 8
  fi
  if ! bp_member_event_record "admin:$rev:$user" "$now" "$user" delete 0 0 "$source" ""; then
    bp_paid_abort
    return 8
  fi
  bp_paid_commit || return 8
  printf '%s' "$rev"
}

# event_id timestamp username kind delta result source detail
bp_member_event_record() {
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'     "$(bp_member_clean "$1")" "$2" "$(bp_member_clean "$3")" "$(bp_member_clean "$4")"     "$5" "$6" "$(bp_member_clean "$7")" "$(bp_member_clean "$8")" >> "$BP_MEMBER_EVENTS" || return 8
  chmod 600 "$BP_MEMBER_EVENTS" || return 8
  max="$(bp_cfg member_event_history 2>/dev/null || true)"
  case "$max" in ''|*[!0-9]*) max=2048;; esac
  [ "$max" -ge 128 ] 2>/dev/null || max=128
  [ "$max" -le 10000 ] 2>/dev/null || max=10000
  # Only NONFINANCIAL audit entries are age-trimmed. Paid add,
  # subtract, restore, set and transfer receipts remain retained so a
  # successfully acknowledged legacy ID cannot be silently reaccepted.
  nonfin="$(awk -F '\t' '$4!="add" && $4!="subtract" && $4!="set" && $4!="restore_all" && $4!="transfer" {c++} END {print c+0}' "$BP_MEMBER_EVENTS")" || return 1
  if [ "$nonfin" -gt "$max" ] 2>/dev/null; then
    skip=$((nonfin-max))
    tmp="$BP_STATE/.member-events.$(bp_tmp_suffix)"
    if ! awk -F '\t' -v skip="$skip" '
      $4=="add" || $4=="subtract" || $4=="set" || $4=="restore_all" || $4=="transfer" {print; next}
      skip>0 {skip--; next}
      {print}
    ' "$BP_MEMBER_EVENTS" > "$tmp"; then
      rm -f "$tmp"; return 1
    fi
    if ! chmod 600 "$tmp" || ! mv "$tmp" "$BP_MEMBER_EVENTS"; then
      rm -f "$tmp"; return 1
    fi
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
