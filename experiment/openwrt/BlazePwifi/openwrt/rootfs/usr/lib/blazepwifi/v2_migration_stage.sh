#!/bin/sh
# Operator-only, inactive candidate: full v1 archive plus a member/rental v2
# opening ledger. Never installs a ledger, imports Wi-Fi value, or issues ACK.
set -eu
export LC_ALL=C
reject() { printf 'V2-MIGRATION-STAGE REJECT %s; paid_ack_authorized=0; migration_authorized=0\n' "$1" >&2; exit 8; }
regular() { [ -f "$1" ] && [ ! -L "$1" ]; }
complete() {
  [ ! -s "$1" ] && return 0
  [ "$(tail -c 1 "$1" | od -An -tu1 | tr -d '[:space:]')" = 10 ]
}

[ "$#" -eq 2 ] && [ "$1" = --stage ] &&
  [ "$2" = --operator-quiesced ] || reject explicit_operator_quiescence_required
BP_STATE=${BP_STATE:-/etc/blazepwifi/state}
BP_RUN=${BP_RUN:-/tmp/blazepwifi}
BP_SNAPSHOT_ROOT=${BP_SNAPSHOT_ROOT:-}
[ -n "$BP_SNAPSHOT_ROOT" ] || reject snapshot_storage_required
[ -d "$BP_STATE" ] && [ ! -L "$BP_STATE" ] || reject state_directory
[ -d "$BP_RUN" ] && [ ! -L "$BP_RUN" ] || reject runtime_directory
[ -d "$BP_SNAPSHOT_ROOT" ] && [ ! -L "$BP_SNAPSHOT_ROOT" ] || reject snapshot_directory
state="$(CDPATH= cd -P -- "$BP_STATE" && pwd)" || reject state_directory
run="$(CDPATH= cd -P -- "$BP_RUN" && pwd)" || reject runtime_directory
dest="$(CDPATH= cd -P -- "$BP_SNAPSHOT_ROOT" && pwd)" || reject snapshot_directory
case "$dest/" in "$state/"*) reject recursive_snapshot_storage;; esac
case "$state/" in "$dest/"*) reject state_inside_snapshot_storage;; esac
uid="$(id -u)" || reject owner
[ "$(stat -c '%a:%u' "$state")" = "700:$uid" ] || reject state_private
[ "$(stat -c '%a:%u' "$run")" = "700:$uid" ] || reject runtime_private
[ "$(stat -c '%a:%u' "$dest")" = "700:$uid" ] || reject snapshot_private
lock="$run/paid-financial.lock"
regular "$lock" || reject writer_lock
case "$(stat -c '%a:%h:%u' "$lock")" in
  400:1:"$uid"|440:1:"$uid"|444:1:"$uid"|600:1:"$uid"|640:1:"$uid"|644:1:"$uid") ;;
  *) reject writer_lock_metadata;;
esac
exec 6<"$lock" || reject writer_lock
flock -n 6 || reject writer_busy
marker="$state/paid-v2-cutover-intent"
regular "$marker" || reject frozen_marker_required
[ ! -e "$state/paid-state-uncertain" ] &&
  [ ! -L "$state/paid-state-uncertain" ] || reject unresolved_paid_write
archive_dir="$dest/v1-frozen-snapshot"
archive="$archive_dir/state.tar"
regular "$archive" && regular "$archive_dir/SHA256SUMS" || reject frozen_archive_required
[ -d "$archive_dir" ] && [ ! -L "$archive_dir" ] || reject frozen_archive_directory
[ "$(stat -c '%a:%u' "$archive_dir")" = "700:$uid" ] || reject frozen_archive_private
archive_hash="$(sha256sum "$archive" | awk '{print $1}')" || reject archive_digest
[ "$(cat "$archive_dir/SHA256SUMS")" = "$archive_hash  state.tar" ] || reject archive_digest_mismatch
tmp="$dest/.v1-v2-candidate.tmp"
final="$dest/v1-v2-candidate"
[ ! -e "$tmp" ] && [ ! -L "$tmp" ] || reject incomplete_candidate_present
[ ! -e "$final" ] && [ ! -L "$final" ] || reject prior_candidate_present

# All source reads remain under the installed financial writer lock. Do not
# infer that a matching SHA-256 archive is fresh against an external witness.
required='accounts.tsv vouchers.tsv members.tsv member-events.tsv member-revision rental-devices.tsv rental-events.tsv'
for name in $required; do
  path="$state/$name"
  regular "$path" || reject missing_or_special_source
  [ "$(stat -c '%a:%h:%u' "$path")" = "600:1:$uid" ] || reject source_metadata
  complete "$path" || reject partial_record
done
for name in credits.tsv sessions.tsv; do
  path="$state/$name"
  if [ -e "$path" ] || [ -L "$path" ]; then
    regular "$path" && [ ! -s "$path" ] || reject unsupported_legacy_money
  fi
done
[ ! -s "$state/vouchers.tsv" ] || reject unsupported_voucher_money
[ -d "$state/targets" ] && [ ! -L "$state/targets" ] || reject target_directory
for path in "$state/targets"/* "$state/targets"/.[!.]* "$state/targets"/..?*; do
  if [ -e "$path" ] || [ -L "$path" ]; then reject unresolved_coin_window; fi
done
set --
for name in $required; do set -- "$@" "$state/$name"; done
before="$(sha256sum "$@")" || reject source_digest
umask 077
mkdir "$tmp" || reject stage_directory
for name in $required; do
  tar -xOf "$archive" "./$name" > "$tmp/$name" || reject archive_member_missing
  cmp -s "$state/$name" "$tmp/$name" || reject archive_source_mismatch
done
for name in accounts.tsv members.tsv rental-devices.tsv member-events.tsv rental-events.tsv; do
  [ "$(stat -c '%s' "$tmp/$name")" -le 16777216 ] || reject source_too_large
done
awk -F '\t' '
  function num(v) {return v ~ /^(0|[1-9][0-9]*)$/ && length(v)<=10 && v+0<=2147483647}
  NF!=9 || length($1)<2 || length($1)>96 || $1 !~ /^[A-Za-z0-9_.:-]+$/ ||
    ++seen[$1]>1 || !num($2) || !num($3) || !num($4) ||
    $5 !~ /^(0|1)$/ || !num($6) {bad=1}
  $2!=0 || $3!=0 || $4!=0 || $5!=0 || $6!=0 || $9!="" {money=1}
  END {if (bad || money) exit 8}
' "$tmp/accounts.tsv" || reject unsupported_or_corrupt_wifi_money
revision="$(cat "$tmp/member-revision")" || reject member_revision
case "$revision" in 0|[1-9]*) ;; *) reject member_revision;; esac
case "$revision" in *[!0-9]*) reject member_revision;; esac
[ "${#revision}" -le 10 ] && [ "$revision" -le 2147483647 ] 2>/dev/null || reject member_revision
awk -F '\t' -v rev="$revision" '
  function num(v,max) {return v ~ /^(0|[1-9][0-9]*)$/ && length(v)<=10 && v+0<=max}
  NF!=11 || length($1)<2 || length($1)>32 ||
    $1 !~ /^[A-Za-z0-9_.-]+$/ || ++seen[$1]>1 ||
    $3 !~ /^(0|1)$/ || !num($7,20000) || !num($8,2147483647) ||
    !num($9,rev) || !num($10,2147483647) {bad=1}
  END {if (bad || NR>512) exit 8}
' "$tmp/members.tsv" || reject member_corrupt_or_out_of_range
awk -F '\t' '
  function num(v) {return v ~ /^(0|[1-9][0-9]*)$/ && length(v)<=10 && v+0<=2147483647}
  NF!=5 || length($1)<2 || length($1)>96 ||
    $1 !~ /^[A-Za-z0-9_.:-]+$/ || ++seen[$1]>1 ||
    $2=="" || !num($3) || !num($5) {bad=1}
  END {if (bad || NR>512) exit 8}
' "$tmp/rental-devices.tsv" || reject rental_corrupt_or_out_of_range
# Retain every v1 receipt byte in state.tar. No historical event is converted
# to a v2 controller sequence, and no assertion of complete v1 history is made.
# PAY-0766: stages preserve old receipts but MUST NOT bind them to a new
# username epoch or invent a transfer recipient. Check the full retained
# paid history against current members under the pre-existing paid lock.
# This remains an INACTIVE archive candidate, never a migration admission.
# Nonfinancial v1 create/delete rows can be trimmed; lack of a lifecycle
# row is NOT proof of stable provenance. Owner mapping remains required.
awk -F '\t' '
  FILENAME==ARGV[1] {members[$1]=1; next}
  $4=="create" {
    if ($3 in paid_ref) bad=1
    if (++creates[$3]>1) reused[$3]=1
  }
  $4=="delete" {deleted[$3]=1}
  NF!=8 || $1=="" || $2 !~ /^[0-9]+$/ || $3=="" ||
    $4=="" || $5 !~ /^-?[0-9]+$/ || $6 !~ /^[0-9]+$/ ||
    $7=="" {bad=1}
  {if (++seen[$1]>1) bad=1}
  $4=="add" || $4=="subtract" || $4=="set" ||
  $4=="restore_all" || $4=="transfer" {
    paid_ref[$3]=1
    d=$5; if (substr(d,1,1)=="-") d=substr(d,2)
    if (length(d)>10 || d+0>2147483647 ||
        $5 !~ /^-?[0-9]+$/ || $6 !~ /^(0|[1-9][0-9]*)$/ ||
        length($6)>10 || $6+0>2147483647 ||
        !($3 in members)) bad=1
    # PAY-0767: a retained old receipt result alone is not proof
    # that its delta and kind are consistent with the actual v1 writer.
    # Reject contradictory money before preparing any inactive opening.
    if ($4=="add" &&
        ($5 !~ /^(0|[1-9][0-9]*)$/ || $5+0!=$6+0)) bad=1
    if (($4=="subtract" || $4=="restore_all" || $4=="transfer") &&
        ($5 !~ /^-(0|[1-9][0-9]*)$/ ||
         -($5+0)!=$6+0 || ($4=="transfer" && $6+0==0))) bad=1
    if ($4=="set" &&
        ($5 !~ /^-?(0|[1-9][0-9]*)$/ ||
         $6+0-($5+0)<0 || $6+0-($5+0)>2147483647)) bad=1
    # PAY-0769: older legitimate nontransfer v1 paid receipts may
    # have an empty optional detail; preserve that compatibility.
    # When detail is present the real v1 writer records post-balance.
    if (($4=="add" || $4=="subtract" || $4=="set" ||
         $4=="restore_all") && $8!="") {
      if ($8 !~ /^(0|[1-9][0-9]*)$/ ||
          length($8)>10 || $8+0>2147483647) bad=1
      else if (($4=="add" && $8+0<$6+0) ||
               ($4=="subtract" && $8+0+$6+0>2147483647) ||
               ($4=="set" && $8+0!=$6+0) ||
               ($4=="restore_all" && $8!="0")) bad=1
    }
    if ($4=="transfer") {
      n=split($8,p,":")
      if (n==3) paid_ref[p[2]]=1
      if (n!=3 || !(p[2] in members) || p[2]==$3 ||
          p[1] !~ /^(0|[1-9][0-9]*)$/ ||
          p[3] !~ /^(0|[1-9][0-9]*)$/ ||
          length(p[1])>10 || length(p[3])>10 ||
          p[1]+0>2147483647 || p[3]+0>2147483647 ||
          p[1]+0+$6+0>2147483647 || p[3]+0<$6+0)
          bad=1
    }
  }
  END {
    for (u in paid_ref)
      if ((u in deleted) || (u in reused)) bad=1
    if (bad) exit 8
  }
' "$tmp/members.tsv" "$tmp/member-events.tsv" || reject member_receipt_corrupt
awk -F '\t' '
  FILENAME==ARGV[1] {device[$1]=1; next}
  NF!=5 || $1=="" || $4 !~ /^[0-9]+$/ {bad=1}
  $1 ~ /^r:/ {
    digest=substr($1,3)
    if (length(digest)!=64 || digest ~ /[^0-9a-f]/ ||
        !($2 in device) || $3 !~ /^(0|[1-9][0-9]*)$/ ||
        length($3)>10 || $3+0>2147483647 ||
        length($4)>10 || $4+0>2147483647 ||
        $5 !~ /^p:([1-9]|1[0-9]|20)$/) bad=1
  }
  {if (++seen[$1]>1) bad=1}
  END {if (bad) exit 8}
' "$tmp/rental-devices.tsv" "$tmp/rental-events.tsv" || reject rental_receipt_corrupt

ledger="$tmp/ledger.tsv"
printf 'V\t2\nP\t%s\t%s\n' "$archive_hash" "$revision" > "$ledger" || reject stage_write
awk -F '\t' '{printf "A\t%s\t%s\n",$1,$8}' "$tmp/members.tsv" >> "$ledger" || reject stage_write
awk -F '\t' '{printf "L\t%s\t%s\n",$1,$3}' "$tmp/rental-devices.tsv" >> "$ledger" || reject stage_write
ledger_hash="$(sha256sum "$ledger" | awk '{print $1}')" || reject stage_digest
printf 'H\t%s\n' "$ledger_hash" >> "$ledger" || reject stage_write
cp "$archive" "$tmp/state.tar" || reject stage_archive_copy
[ "$(sha256sum "$tmp/state.tar" | awk '{print $1}')" = "$archive_hash" ] || reject stage_archive_mismatch
printf '%s  %s\n' "$archive_hash" state.tar > "$tmp/SHA256SUMS" || reject stage_write
printf '%s  %s\n' "$(sha256sum "$ledger" | awk '{print $1}')" ledger.tsv >> "$tmp/SHA256SUMS" || reject stage_write
(cd "$tmp" && sha256sum -c SHA256SUMS >/dev/null) || reject stage_digest
after="$(sha256sum "$@")" || reject source_digest
[ "$before" = "$after" ] || reject concurrent_source_change
regular "$marker" || reject frozen_marker_changed
[ ! -e "$state/paid-state-uncertain" ] &&
  [ ! -L "$state/paid-state-uncertain" ] || reject unresolved_paid_write
[ "$(sha256sum "$archive" | awk '{print $1}')" = "$archive_hash" ] || reject archive_changed
sync || reject stage_sync_uncertain
mv "$tmp" "$final" || reject stage_rename_uncertain
sync || reject stage_sync_uncertain
printf 'V2-MIGRATION-STAGE CANDIDATE sha256=%s; paid_ack_authorized=0; migration_authorized=0; physical_durability_verified=0\n' "$archive_hash"
