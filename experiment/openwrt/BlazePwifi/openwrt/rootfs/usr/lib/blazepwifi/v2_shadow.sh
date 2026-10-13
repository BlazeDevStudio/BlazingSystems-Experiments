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
  *":1:$source_uid:400"|*":1:$source_uid:440"|*":1:$source_uid:444"|
  *":1:$source_uid:600"|*":1:$source_uid:640"|*":1:$source_uid:644") ;;
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

# All three authoritative v1 sources must be independently well-formed.
for name in accounts.tsv members.tsv rental-devices.tsv; do
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
# A two-pass fingerprint detects most concurrent source changes, but cannot
# prove a transaction-consistent snapshot across three independently written
# v1 files. Never use these results to create/migrate actual paid balances.
before="$(sha256sum "$state/accounts.tsv" "$state/members.tsv" "$state/rental-devices.tsv" 2>/dev/null)" || {
  echo 'SHADOW BLOCKED: source fingerprint read failed' >&2; exit 8;
}
account_count="$(awk -F '\t' '
  {
    if (NF!=9 || $1 !~ /^[A-Za-z0-9_.:-]+$/ || length($1)>96 ||
        $2 !~ /^[0-9]+$/ || $3 !~ /^[0-9]+$/ ||
        $4 !~ /^[0-9]+$/ || $5 !~ /^(0|1)$/ ||
        $6 !~ /^[0-9]+$/ || ++seen[$1]>1) bad=1
    count++
  }
  END {if (bad) exit 8; print count+0}
' "$state/accounts.tsv")" || {
  echo 'SHADOW BLOCKED: invalid/duplicate Wi-Fi paid account row' >&2; exit 8;
}
member_count="$(awk -F '\t' '
  {
    if (NF!=11 || $1 !~ /^[A-Za-z0-9_.-]+$/ || length($1)>32 ||
        $3 !~ /^(0|1)$/ || $7 !~ /^[0-9]+$/ ||
        $8 !~ /^[0-9]+$/ || $9 !~ /^[0-9]+$/ ||
        $10 !~ /^[0-9]+$/ || ++seen[$1]>1) bad=1
    count++
  }
  END {if (bad) exit 8; print count+0}
' "$state/members.tsv")" || {
  echo 'SHADOW BLOCKED: invalid/duplicate paid member row' >&2; exit 8;
}
rental_count="$(awk -F '\t' '
  {
    if (NF!=5 || $1 !~ /^[A-Za-z0-9_.:-]+$/ ||
        length($1)>96 || length($2)==0 ||
        $3 !~ /^[0-9]+$/ || $5 !~ /^[0-9]+$/ ||
        ++seen[$1]>1) bad=1
    count++
  }
  END {if (bad) exit 8; print count+0}
' "$state/rental-devices.tsv")" || {
  echo 'SHADOW BLOCKED: invalid/duplicate paid rental lease row' >&2; exit 8;
}
after="$(sha256sum "$state/accounts.tsv" "$state/members.tsv" "$state/rental-devices.tsv" 2>/dev/null)" || {
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
