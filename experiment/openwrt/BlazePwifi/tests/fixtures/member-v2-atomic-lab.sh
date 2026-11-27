#!/bin/sh
# PAY-0713 — synthetic-only member balance+receipt authority.
# Routes through real bp_member_balance_change / bp_member_transfer entrypoints
# ONLY with BP_MEMBER_V2_LAB=1 and private, marker-gated /tmp fixture.
# No live importer, migration, paid CGI, target fsync or rollback witness.
# members/events/revision TSVs are derived, NEVER authoritative in lab mode.

bp_member_v2_lab_guard() {
  [ "${BP_MEMBER_V2_LAB:-0}" = 1 ] || return 9
  case "$BP_STATE" in /tmp/blaze-v2-member-*/state) ;; *) return 9;; esac
  root="${BP_STATE%/state}"; suffix="${root#/tmp/blaze-v2-member-}"
  case "$suffix" in ''|*/*|*..*|*[!A-Za-z0-9]*) return 9;; esac
  [ "$BP_RUN" = "$root/run" ] &&
    [ "$BP_MEMBERS" = "$BP_STATE/members.tsv" ] &&
    [ "$BP_MEMBER_EVENTS" = "$BP_STATE/member-events.tsv" ] &&
    [ "$BP_MEMBER_REVISION" = "$BP_STATE/member-revision" ] || return 9
  [ -d "$root" ] && [ ! -L "$root" ] &&
    [ -d "$BP_STATE" ] && [ ! -L "$BP_STATE" ] &&
    [ -d "$BP_RUN" ] && [ ! -L "$BP_RUN" ] || return 9
  owner="$(id -u)" || return 9
  for dir in "$root" "$BP_STATE" "$BP_RUN"; do
    [ "$(stat -c '%a:%u' "$dir" 2>/dev/null)" = "700:$owner" ] || return 9
  done
  marker="$root/.blaze-v2-member-synthetic-only"
  [ -f "$marker" ] && [ ! -L "$marker" ] &&
    [ "$(stat -c '%a:%h:%u' "$marker" 2>/dev/null)" = "600:1:$owner" ] &&
    [ "$(cat "$marker" 2>/dev/null)" = BLAZE-V2-MEMBER-SYNTHETIC-ONLY ] || return 9
  BP_MEMBER_V2_LAB_FILE="$BP_STATE/member-v2-atomic.tsv"
  [ ! -e "$BP_STATE/paid-state-uncertain" ] &&
    [ ! -L "$BP_STATE/paid-state-uncertain" ] || return 9
}
bp_member_v2_lab_valid_body() {
  awk -F '\t' '
    function uint(x,max) {return x ~ /^(0|[1-9][0-9]*)$/ && length(x)<=10 && x+0<=max}
    NR==1 {if(NF!=2||$1!="V"||$2!="1") bad=1; next}
    NR==2 {if(NF!=2||$1!="Q"||!uint($2,2147483647)) bad=1; revision=$2+0; next}
    $1=="M" {
      if(NF!=12||$2!~/^[A-Za-z0-9_.-]+$/||length($2)<2||length($2)>32||
         ++names[$2]>1||$4!~/^(0|1)$/||!uint($8,2147483647)||
         !uint($9,2147483647)||!uint($10,2147483647)||$10+0>revision) bad=1
      count++; next
    }
    $1=="R" {
      if(NF!=9||length($2)<1||length($2)>96||++events[$2]>1||
         !uint($7,2147483647)) bad=1
      next
    }
    {bad=1}
    END {if(NR<3||count<1||bad) exit 8}
  ' "$1"
}
bp_member_v2_lab_verify() {
  file="$BP_MEMBER_V2_LAB_FILE"
  [ -f "$file" ] && [ ! -L "$file" ] &&
    [ "$(stat -c '%a:%h:%u' "$file" 2>/dev/null)" = "600:1:$(id -u)" ] || return 9
  bytes="$(wc -c < "$file" 2>/dev/null)" || return 9
  case "$bytes" in ''|*[!0-9]*) return 9;; esac
  [ "$bytes" -ge 18 ] && [ "$bytes" -le 2097152 ] || return 9
  last="$(tail -n 1 "$file")" || return 9
  printf '%s\n' "$last" | grep -Eq '^H[[:space:]][0-9a-f]{64}$' || return 9
  expected="$(printf '%s' "$last" | cut -f2)"
  digest="$(sed '$d' "$file" | sha256sum | cut -d' ' -f1)" || return 9
  [ "$expected" = "$digest" ] || return 9
  body="$BP_STATE/.v2-verify-$$"
  sed '$d' "$file" >"$body" || { rm -f "$body"; return 9; }
  bp_member_v2_lab_valid_body "$body"; result=$?
  rm -f "$body"
  [ "$result" -eq 0 ] || return 9
}
bp_member_v2_lab_seal() {
  bp_member_v2_lab_valid_body "$1" || return 9
  digest="$(sha256sum "$1" | cut -d' ' -f1)" || return 9
  printf 'H\t%s\n' "$digest" >>"$1" || return 9
  chmod 600 "$1" && sync
}
bp_member_v2_lab_project() {
  phase="$1"
  [ "$phase" != after ] ||
    [ "${BP_MEMBER_V2_LAB_FAULT:-}" != projection-eio ] || return 8
  members="$BP_STATE/.v2-members-$$"; events="$BP_STATE/.v2-events-$$"
  revision="$BP_STATE/.v2-revision-$$"
  if ! awk -F '\t' '$1=="M" {sub(/^M\t/,"");print}' "$BP_MEMBER_V2_LAB_FILE" >"$members" ||
     ! awk -F '\t' '$1=="R" {sub(/^R\t/,"");print}' "$BP_MEMBER_V2_LAB_FILE" >"$events" ||
     ! awk -F '\t' '$1=="Q" {print $2}' "$BP_MEMBER_V2_LAB_FILE" >"$revision" ||
     ! chmod 600 "$members" "$events" "$revision" || ! sync; then
    rm -f "$members" "$events" "$revision"; return 8
  fi
  if ! mv "$members" "$BP_MEMBERS" || ! mv "$events" "$BP_MEMBER_EVENTS" ||
     ! mv "$revision" "$BP_MEMBER_REVISION" || ! sync; then
    rm -f "$members" "$events" "$revision"; return 8
  fi
}
# No implicit seed: synthetic setup must explicitly call this, once.
bp_member_v2_lab_seed() (
  bp_member_v2_lab_guard || exit 9
  [ ! -e "$BP_MEMBER_V2_LAB_FILE" ] && [ ! -L "$BP_MEMBER_V2_LAB_FILE" ] || exit 9
  exec 6>"$BP_RUN/paid-financial.lock" || exit 9
  flock -n 6 || exit 8
  [ -f "$BP_MEMBERS" ] && [ ! -L "$BP_MEMBERS" ] &&
    [ -f "$BP_MEMBER_EVENTS" ] && [ ! -L "$BP_MEMBER_EVENTS" ] &&
    [ -f "$BP_MEMBER_REVISION" ] && [ ! -L "$BP_MEMBER_REVISION" ] || exit 9
  rev="$(cat "$BP_MEMBER_REVISION")" || exit 9
  tmp="$BP_STATE/.v2-seed-$$"; umask 077
  {
    printf 'V\t1\nQ\t%s\n' "$rev"
    awk '{print "M\t"$0}' "$BP_MEMBERS"
    awk '{print "R\t"$0}' "$BP_MEMBER_EVENTS"
  } >"$tmp" || exit 9
  bp_member_v2_lab_seal "$tmp" || { rm -f "$tmp"; exit 9; }
  [ ! -e "$BP_MEMBER_V2_LAB_FILE" ] || exit 9
  mv "$tmp" "$BP_MEMBER_V2_LAB_FILE" || exit 9
  sync || exit 9
  bp_member_v2_lab_verify || exit 9
  bp_member_v2_lab_project after || exit 9
)
bp_member_v2_lab_dispatch() (
  bp_member_v2_lab_guard || exit 9
  exec 6>"$BP_RUN/paid-financial.lock" || exit 9
  flock -n 6 || exit 8
  bp_member_v2_lab_verify || exit 9
  # Repair interrupted projections BEFORE any replay/new financial operation.
  bp_member_v2_lab_project before || exit 8
  action="$1"; shift
  case "$action" in
    balance)
      user="$(bp_member_norm "$1")" || exit 2
      kind="$2"; units="$3"; source="$(bp_member_clean "$4")"; event="$5"; target=""
      case "$kind" in add|subtract|set|restore_all) ;; *) exit 2;; esac
      bp_member_safe_seconds "$units" 31536000 || exit 2;;
    transfer)
      user="$(bp_member_norm "$1")" || exit 2
      target="$(bp_member_norm "$2")" || exit 2
      [ "$user" != "$target" ] || exit 2
      units="$3"; source="$(bp_member_clean "$4")"; event="$5"; kind=transfer
      bp_member_safe_seconds "$units" 31536000 && [ "$units" -gt 0 ] || exit 2;;
    *) exit 2;;
  esac
  rev="$(awk -F '\t' '$1=="Q" {print $2}' "$BP_MEMBER_V2_LAB_FILE")" || exit 9
  if [ -z "$event" ]; then
    if [ "$kind" = transfer ]; then event="admin:$((rev+1)):$user>$target"
    else event="admin:$((rev+1)):$user"; fi
  fi
  printf '%s\n' "$event" | grep -Eq '^[A-Za-z0-9_.:>-]{1,96}$' || exit 2
  receipt="$(awk -F '\t' -v e="$event" '$1=="R"&&$2==e {print;exit}' "$BP_MEMBER_V2_LAB_FILE")" || exit 9
  if [ -n "$receipt" ]; then
    old_user="$(printf '%s' "$receipt" | cut -f4)"
    old_kind="$(printf '%s' "$receipt" | cut -f5)"
    old_result="$(printf '%s' "$receipt" | cut -f7)"
    old_source="$(printf '%s' "$receipt" | cut -f8)"
    old_detail="$(printf '%s' "$receipt" | cut -f9)"
    [ "$old_user" = "$user" ] && [ "$old_kind" = "$kind" ] &&
      [ "$old_source" = "$source" ] || exit 5
    case "$kind" in add|subtract|set|transfer)
      [ "$old_result" = "$units" ] || exit 5;; esac
    if [ "$kind" = transfer ]; then
      old_target="$(printf '%s' "$old_detail" | awk -F: 'NF==3 {print $2}')"
      [ "$old_target" = "$target" ] || exit 5
    fi
    printf '%s\t%s\n' "$old_result" "$rev"
    exit 0
  fi
  balance="$(awk -F '\t' -v u="$user" '$1=="M"&&$2==u {print $9}' "$BP_MEMBER_V2_LAB_FILE")"
  [ -n "$balance" ] || exit 3
  bp_member_safe_seconds "$balance" 2147483647 || exit 9
  case "$kind" in
    add)
      [ "$balance" -le $((2147483647-units)) ] || exit 8
      new_from=$((balance+units)); delta="$units"; result="$units"; detail="$new_from";;
    subtract)
      [ "$balance" -ge "$units" ] || exit 4
      new_from=$((balance-units)); delta="-$units"; result="$units"; detail="$new_from";;
    set)
      new_from="$units"; delta=$((units-balance)); result="$units"; detail="$new_from";;
    restore_all)
      new_from=0; delta="-$balance"; result="$balance"; detail=0;;
    transfer)
      to_balance="$(awk -F '\t' -v u="$target" '$1=="M"&&$2==u {print $9}' "$BP_MEMBER_V2_LAB_FILE")"
      [ -n "$to_balance" ] || exit 3
      bp_member_safe_seconds "$to_balance" 2147483647 || exit 9
      [ "$balance" -ge "$units" ] || exit 4
      [ "$to_balance" -le $((2147483647-units)) ] || exit 8
      new_from=$((balance-units)); new_to=$((to_balance+units))
      delta="-$units"; result="$units"; detail="$new_from:$target:$new_to";;
  esac
  now="$(bp_now)"; nextrev=$((rev+1))
  [ "$nextrev" -le 2147483647 ] || exit 8
  body="$BP_STATE/.v2-intent-$$"; umask 077
  if ! awk -F '\t' -v OFS='\t' -v u="$user" -v t="$target" \
      -v b="$new_from" -v tb="${new_to:-0}" -v r="$nextrev" -v ts="$now" \
      -v src="$source" -v id="$event" -v k="$kind" -v d="$delta" \
      -v result="$result" -v detail="$detail" '
    $1=="H" {next}
    $1=="Q" {$2=r}
    $1=="M"&&$2==u {$9=b;$10=r;$11=ts;$12=src}
    $1=="M"&&t!=""&&$2==t {$9=tb;$10=r;$11=ts;$12=src}
    {print}
    END {print "R",id,ts,u,k,d,result,src,detail}
  ' "$BP_MEMBER_V2_LAB_FILE" >"$body" || ! bp_member_v2_lab_seal "$body"; then
    rm -f "$body"; exit 8
  fi
  if [ "${BP_MEMBER_V2_LAB_FAULT:-}" = before-authority-rename ]; then
    rm -f "$body"; exit 86
  fi
  mv "$body" "$BP_MEMBER_V2_LAB_FILE" || { rm -f "$body";exit 8; }
  sync || exit 8
  [ "${BP_MEMBER_V2_LAB_FAULT:-}" != after-authority-rename ] || exit 86
  bp_member_v2_lab_project after || exit 8
  printf '%s\t%s\n' "$result" "$nextrev"
)
