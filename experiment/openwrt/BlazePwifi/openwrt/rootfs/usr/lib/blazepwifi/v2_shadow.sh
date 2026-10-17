#!/bin/sh
# SHADOW-0666: installed, manually invoked, READ-ONLY diagnostics.
# NOT a v2 ledger, migration, credit importer, payment ACK or powercut proof.
# Invocation on a device: sh /usr/lib/blazepwifi/v2_shadow.sh status
# UCI blazepwifi.main.v2_shadow_diagnostics defaults to 0. NO cron or CGI.
set -eu
export LC_ALL=C
if [ "$#" -ne 1 ] || [ "$1" != status ]; then
  echo 'SHADOW BLOCKED: status is the only read-only command' >&2
  exit 2
fi
if [ "${BLAZE_V2_SHADOW_FIXTURE:-}" = 1 ]; then
  # Test-only override cannot target mounted, system or arbitrary roots.
  state="${BP_V2_SHADOW_TEST_ROOT:-}"
  case "$state" in
    /tmp/blaze-v2-shadow-*)
      tail="${state#/tmp/blaze-v2-shadow-}"
      case "$tail" in ''|*/*|*..*) echo 'SHADOW BLOCKED: invalid fixture path' >&2; exit 2;; esac
      ;;
    *) echo 'SHADOW BLOCKED: synthetic fixture path required' >&2; exit 2;;
  esac
  # Read only the fixture's pre-existing synthetic money lock.
  run="$state/run"
  marker="$state/.blaze-shadow-fixture-only"
  [ -d "$state" ] && [ ! -L "$state" ] &&
    [ -f "$marker" ] && [ ! -L "$marker" ] &&
    [ "$(cat "$marker" 2>/dev/null)" = 'BLAZE-SHADOW-READ-ONLY-FIXTURE' ] ||
      { echo 'SHADOW BLOCKED: synthetic fixture marker missing' >&2; exit 2; }
else
  [ -z "${BP_V2_SHADOW_TEST_ROOT:-}" ] || {
    echo 'SHADOW BLOCKED: fixture override disabled on device' >&2; exit 2;
  }
  [ "$(id -u)" = 0 ] || {
    echo 'SHADOW BLOCKED: root-only local diagnostics' >&2; exit 3;
  }
  command -v uci >/dev/null 2>&1 || {
    echo 'SHADOW BLOCKED: UCI unavailable' >&2; exit 3;
  }
  [ "$(uci -q get blazepwifi.main.v2_shadow_diagnostics 2>/dev/null || true)" = 1 ] ||
    { echo 'SHADOW DISABLED: explicit UCI opt-in required' >&2; exit 3; }
  state=/etc/blazepwifi/state
  run=/tmp/blazepwifi
fi

# Unlike bp_init_dirs, this utility must NEVER touch, chmod, repair, create,
# migrate, stage, delete, or rewrite a financial file.
[ -d "$state" ] && [ ! -L "$state" ] || {
  echo 'SHADOW BLOCKED: financial state directory missing/unsafe' >&2; exit 8;
}
# SHADOW-0667: the observer must not treat foreign, linked or broadly
# accessible financial files as independently trustworthy migration sources.
# Use only BusyBox-compatible stat fields. No chmod, mkdir, touch or repair.
# Root on appliances / calling uid for marker-gated synthetic fixtures.
source_uid="$(id -u)" || exit 8
[ "$(stat -c '%a:%u' "$state" 2>/dev/null)" = "700:$source_uid" ] || {
  echo 'SHADOW BLOCKED: financial state directory ownership/mode unsafe' >&2; exit 8;
}
[ ! -e "$state/paid-state-uncertain" ] && [ ! -L "$state/paid-state-uncertain" ] || {
  echo 'SHADOW BLOCKED: paid-state uncertainty requires operator reconciliation' >&2; exit 9;
}
# MIG-0735: a two-pass fingerprint alone does NOT make this a stable
# source read. All installed v1 paid mutation/replay paths share this lock.
# Never create or chmod any lock/state file: if no existing safe descriptor
# can be held, diagnostics must fail closed rather than claim quiescence.
[ ! -e "$state/paid-v2-cutover-intent" ] &&
  [ ! -L "$state/paid-v2-cutover-intent" ] || {
  echo 'SHADOW BLOCKED: paid authority cutover marker present' >&2; exit 9;
}
[ -d "$run" ] && [ ! -L "$run" ] &&
  [ "$(stat -c '%a:%u' "$run" 2>/dev/null)" = "700:$source_uid" ] || {
  echo 'SHADOW BLOCKED: private paid-lock directory missing/unsafe' >&2; exit 8;
}
money_lock="$run/paid-financial.lock"
[ -f "$money_lock" ] && [ ! -L "$money_lock" ] || {
  echo 'SHADOW BLOCKED: paid writer lock file missing/linked' >&2; exit 8;
}
lock_identity="$(stat -c '%d:%i:%h:%u:%a' "$money_lock" 2>/dev/null)" || {
  echo 'SHADOW BLOCKED: paid writer lock metadata unreadable' >&2; exit 8;
}
# Legacy bp_paid_begin creates this file with its process umask (commonly
# 0644); the containing run directory MUST be 0700, file has exactly
# one link, belongs to this operator and cannot be writable by peers.
case "$lock_identity" in
  *":1:$source_uid:400"|*":1:$source_uid:440"|*":1:$source_uid:444"|*":1:$source_uid:600"|*":1:$source_uid:640"|*":1:$source_uid:644") ;;
  *) echo 'SHADOW BLOCKED: unsafe paid writer lock inode/permissions' >&2; exit 8;;
esac
exec 7< "$money_lock" || {
  echo 'SHADOW BLOCKED: paid writer lock cannot be opened read-only' >&2; exit 8;
}
command -v flock >/dev/null 2>&1 && flock -n 7 || {
  echo 'SHADOW BLOCKED: paid financial writer active or no flock' >&2; exit 9;
}
[ "$lock_identity" = "$(stat -c '%d:%i:%h:%u:%a' "$money_lock" 2>/dev/null)" ] || {
  echo 'SHADOW BLOCKED: paid lock inode replaced during acquisition' >&2; exit 8;
}

# MIG-0736: a monetary source is NOT just the three materialized balances.
# The revision floor and both replay/receipt stores are indispensable for
# detecting disputed paid time during any future cutover. No repair/create.
for name in accounts.tsv members.tsv rental-devices.tsv member-revision member-events.tsv rental-events.tsv; do
  f="$state/$name"
  [ -f "$f" ] && [ -r "$f" ] && [ ! -L "$f" ] || {
    echo "SHADOW BLOCKED: missing/unsafe $name" >&2; exit 8;
  }
  # Regular private files must have exactly one hardlink and be owned by the
  # executing root/operator. Identical contents do NOT establish inode trust.
  [ "$(stat -c '%a:%h:%u' "$f" 2>/dev/null)" = "600:1:$source_uid" ] || {
    echo "SHADOW BLOCKED: linked or broadly accessible $name" >&2; exit 8;
  }
done
# No PII, HMAC/private key, device identifiers or full file digest is printed.
# A two-pass fingerprint detects concurrent source changes, but cannot prove
# a crash-atomic migration or independent replay freshness. Keep all six v1
# monetary source files inside the SAME two-pass observation and lock.
before="$(sha256sum "$state/accounts.tsv" "$state/members.tsv" "$state/rental-devices.tsv" "$state/member-revision" "$state/member-events.tsv" "$state/rental-events.tsv" 2>/dev/null)" || {
  echo 'SHADOW BLOCKED: source fingerprint read failed' >&2; exit 8;
}
# MIG-0746: the v1 paid credit, lease and paused-time fields are
# migration-critical arithmetic, not merely strings of digits.  Accept
# canonical zero or positive signed-32-bit values only.  Do not guess
# balance zero, wrap numeric conversions, or approve an unsafe cutover.
account_count="$(awk -F '\t' '
  function paid32(v) {
    return v ~ /^(0|[1-9][0-9]*)$/ &&
           length(v)<=10 && v+0<=2147483647
  }
  {
    if (NF!=9 || $1 !~ /^[A-Za-z0-9_.:-]+$/ || length($1)>96 ||
        !paid32($2) || !paid32($3) ||
        !paid32($4) || $5 !~ /^(0|1)$/ ||
        !paid32($6) || ++seen[$1]>1) bad=1
    count++
  }
  END {if (bad) exit 8; print count+0}
' "$state/accounts.tsv")" || {
  echo 'SHADOW BLOCKED: invalid/duplicate Wi-Fi paid account row' >&2; exit 8;
}
member_count="$(awk -F '\t' '
  function paid32(v) {
    return v ~ /^(0|[1-9][0-9]*)$/ &&
           length(v)<=10 && v+0<=2147483647
  }
  {
    if (NF!=11 || $1 !~ /^[A-Za-z0-9_.-]+$/ || length($1)>32 ||
        $3 !~ /^(0|1)$/ || $7 !~ /^[0-9]+$/ ||
        !paid32($8) || $9 !~ /^[0-9]+$/ ||
        !paid32($10) || ++seen[$1]>1) bad=1
    count++
  }
  END {if (bad) exit 8; print count+0}
' "$state/members.tsv")" || {
  echo 'SHADOW BLOCKED: invalid/duplicate paid member row' >&2; exit 8;
}
rental_count="$(awk -F '\t' '
  function paid32(v) {
    return v ~ /^(0|[1-9][0-9]*)$/ &&
           length(v)<=10 && v+0<=2147483647
  }
  {
    if (NF!=5 || $1 !~ /^[A-Za-z0-9_.:-]+$/ ||
        length($1)>96 || length($2)==0 ||
        !paid32($3) || !paid32($5) ||
        ++seen[$1]>1) bad=1
    count++
  }
  END {if (bad) exit 8; print count+0}
' "$state/rental-devices.tsv")" || {
  echo 'SHADOW BLOCKED: invalid/duplicate paid rental lease row' >&2; exit 8;
}
# Member revision and receipts are financial data, not optional UI metadata.
# A missing global counter while paid records exist must NEVER be treated as 0.
[ "$(stat -c '%s' "$state/member-revision" 2>/dev/null)" -le 12 ] 2>/dev/null || {
  echo 'SHADOW BLOCKED: global member revision size invalid' >&2; exit 8;
}
global_rev="$(cat "$state/member-revision" 2>/dev/null)" || {
  echo 'SHADOW BLOCKED: global member revision unreadable' >&2; exit 8;
}
case "$global_rev" in
  0) ;;
  [1-9]*) case "$global_rev" in *[!0-9]*) 
    echo 'SHADOW BLOCKED: invalid global member revision' >&2; exit 8;; esac ;;
  *) echo 'SHADOW BLOCKED: invalid global member revision' >&2; exit 8 ;;
esac
[ "${#global_rev}" -le 10 ] && [ "$global_rev" -le 2147483646 ] 2>/dev/null || {
  echo 'SHADOW BLOCKED: out-of-range member revision' >&2; exit 8;
}
# Pay receipts are capped during normal member operations. Reject implausibly
# large/unreadable files before parsing, instead of hiding an allocation DoS.
for audit_file in member-events.tsv rental-events.tsv; do
  file_size="$(stat -c '%s' "$state/$audit_file" 2>/dev/null)" || exit 8
  [ "$file_size" -le 16777216 ] 2>/dev/null || {
    echo "SHADOW BLOCKED: $audit_file exceeds readonly inspection cap" >&2; exit 8;
  }
done
# Revalidate every account revision against the actual global floor; a
# checksum-consistent, separately restored OLD member-revision is unsafe.
awk -F '\t' -v floor="$global_rev" '
  NF!=11 || $9 !~ /^(0|[1-9][0-9]*)$/ ||
    length($9)>10 || $9+0>floor {bad=1}
  END {if (bad) exit 8}
' "$state/members.tsv" || {
  echo 'SHADOW BLOCKED: member revision exceeds global counter' >&2; exit 8;
}
# MIG-0743/0744: an eventual v2 financial migration cannot trust a
# merely well-formed receipt. Validate the WHOLE retained member corpus
# against existing paid members, not just numeric formatting. An orphaned
# paid source or transfer destination requires operator reconciliation,
# never a guessed balance or synthesized missing member. Historical member
# deletion is valid in v1, but its money receipts cannot be silently
# imported into a v2 read model without an explicit mapping decision.
# Both files are protected by the SAME pre-existing global paid writer lock.
# MIG-0745: usernames are NOT durable paid identities. A delete + recreate
# can rebind old retained paid receipts to a different member epoch, even if
# the username currently exists. The legacy 8-column create/delete audits
# are nonfinancial and may be trimmed. Refuse detectable ambiguity; do not
# assert that absence of such audit rows proves a safe identity migration.
# Readonly SOURCE admission only: no payment, repair, or migration permitted.
awk -F '\t' '
  FILENAME==ARGV[1] {members[$1]=1; next}
  $4=="create" {
    if ($3 in paid_ref) bad=1
    if (++creates[$3]>1) reused[$3]=1
  }
  $4=="delete" {deleted[$3]=1}
  NF!=8 || $1=="" || $2 !~ /^[0-9]+$/ ||
    $3=="" || $4=="" || $5 !~ /^-?[0-9]+$/ ||
    $6 !~ /^[0-9]+$/ || $7=="" {bad=1}
  {if (++seen[$1]>1) bad=1}
  $4=="add" || $4=="subtract" || $4=="set" ||
  $4=="restore_all" || $4=="transfer" {
    paid_ref[$3]=1
    d=$5; if (substr(d,1,1)=="-") d=substr(d,2)
    if (length(d)>10 || d+0>2147483647 ||
        length($6)>10 || $6+0>2147483647 ||
        !($3 in members)) bad=1
    if ($4=="transfer") {
      n=split($8,p,":")
      if (n==3) paid_ref[p[2]]=1
      if (n!=3 || !(p[2] in members) || p[2]==$3 ||
          p[1] !~ /^(0|[1-9][0-9]*)$/ ||
          p[3] !~ /^(0|[1-9][0-9]*)$/ ||
          length(p[1])>10 || length(p[3])>10 ||
          p[1]+0>2147483647 || p[3]+0>2147483647)
        bad=1
    }
    # Non-transfer paid receipt detail is historically optional in v1;
    # preserve the old 8-column empty-final-field format for migration
    # diagnostics rather than imposing a new false receipt failure.
  }
  END {
    for (u in paid_ref)
      if ((u in deleted) || (u in reused)) bad=1
    if (bad) exit 8
  }
' "$state/members.tsv" "$state/member-events.tsv" || {
  echo 'SHADOW BLOCKED: invalid, orphaned, overflowing or duplicate member receipt' >&2; exit 8;
}
# Five columns: event, device, detail/lease, time, audit kind or p:pulses.
# Current installed rental paid events use SHA256-lowercase r:<64-hex>.
# Under a private global money lock require a referenced, extant device and
# a canonical bounded lease, timestamp and 1..20 pulses for migration source
# admission. An orphaned device MUST require operator reconciliation rather
# than a fictitious imported active lease. Nonpaid audit rows are unchanged.
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
' "$state/rental-devices.tsv" "$state/rental-events.tsv" || {
  echo 'SHADOW BLOCKED: invalid, orphaned, overflowing or duplicate paid rental receipt' >&2; exit 8;
}
after="$(sha256sum "$state/accounts.tsv" "$state/members.tsv" "$state/rental-devices.tsv" "$state/member-revision" "$state/member-events.tsv" "$state/rental-events.tsv" 2>/dev/null)" || {
  echo 'SHADOW BLOCKED: source reread failed' >&2; exit 8;
}
[ "$before" = "$after" ] || {
  echo 'SHADOW BLOCKED: source changed during a protected diagnostic' >&2; exit 8;
}
# Keep fd7 locked until the observer has finished all metadata and counts.
[ "$lock_identity" = "$(stat -c '%d:%i:%h:%u:%a' "$money_lock" 2>/dev/null)" ] || {
  echo 'SHADOW BLOCKED: paid lock inode changed while reading sources' >&2; exit 8;
}
printf 'BLAZE_V2_SHADOW_V1\n'
printf 'status=NON_AUTHORITATIVE_READ_ONLY\n'
printf 'wallet_accounts=%s\n' "$account_count"
printf 'member_accounts=%s\n' "$member_count"
printf 'rental_devices=%s\n' "$rental_count"
printf 'migration_authorized=0\n'
printf 'payment_write_authorized=0\n'
printf 'production_durability_verified=0\n'
