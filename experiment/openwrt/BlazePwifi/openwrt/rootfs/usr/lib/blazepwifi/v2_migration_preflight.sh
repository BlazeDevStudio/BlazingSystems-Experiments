#!/bin/sh
# Installed, read-only admission inventory. This does not migrate or authorize payments.
set -eu
BP_STATE=${BP_STATE:-/etc/blazepwifi/state}
BP_RUN=${BP_RUN:-/tmp/blazepwifi}

reject() { printf 'V2-MIGRATION-PREFLIGHT REJECT %s; paid_ack_authorized=0\n' "$1" >&2; exit 8; }
regular() { [ -f "$1" ] && [ ! -L "$1" ]; }
complete() {
  [ ! -s "$1" ] && return 0
  [ "$(tail -c 1 "$1" | od -An -tu1 | tr -d '[:space:]')" = 10 ]
}
sidecars_clear() {
  # Vouchers and legacy MAC balances are value, even when no account row
  # references them. A target or progress file may be an unacknowledged coin
  # window. None has an admitted v2 import/replay representation yet.
  regular "$BP_STATE/vouchers.tsv" || reject voucher_missing_or_special
  [ ! -s "$BP_STATE/vouchers.tsv" ] || reject vouchers_need_import
  for name in credits.tsv sessions.tsv; do
    path="$BP_STATE/$name"
    if [ -e "$path" ] || [ -L "$path" ]; then
      regular "$path" || reject legacy_special
      [ ! -s "$path" ] || reject legacy_money_need_import
    fi
  done
  target_dir="$BP_STATE/targets"
  [ -d "$target_dir" ] && [ ! -L "$target_dir" ] || reject target_directory
  for path in "$target_dir"/* "$target_dir"/.[!.]* "$target_dir"/..?*; do
    if [ -e "$path" ] || [ -L "$path" ]; then
      reject unresolved_coin_window
    fi
  done
}

[ -d "$BP_STATE" ] && [ ! -L "$BP_STATE" ] || reject state_directory
[ -d "$BP_RUN" ] && [ ! -L "$BP_RUN" ] || reject runtime_directory
regular "$BP_STATE/paid-v2-cutover-intent" || reject quiescence_marker
[ ! -e "$BP_STATE/paid-state-uncertain" ] &&
  [ ! -L "$BP_STATE/paid-state-uncertain" ] || reject unresolved_paid_write
regular "$BP_RUN/paid-financial.lock" || reject writer_lock
exec 6<"$BP_RUN/paid-financial.lock" || reject writer_lock
flock -n 6 || reject writer_busy
sidecars_clear

# An absent feature store is legitimate only when its entire family is absent.
regular "$BP_STATE/accounts.tsv" || reject accounts_missing_or_special
member_present=0
for name in members.tsv member-events.tsv member-revision; do
  path="$BP_STATE/$name"
  if [ -e "$path" ] || [ -L "$path" ]; then
    regular "$path" || reject member_special
    member_present=$((member_present+1))
  fi
done
case "$member_present" in 0|3) ;; *) reject member_partial_family;; esac
rental_present=0
for name in rental-devices.tsv rental-events.tsv; do
  path="$BP_STATE/$name"
  if [ -e "$path" ] || [ -L "$path" ]; then
    regular "$path" || reject rental_special
    rental_present=$((rental_present+1))
  fi
done
case "$rental_present" in 0|2) ;; *) reject rental_partial_family;; esac
if [ -e "$BP_STATE/controllers.tsv" ] || [ -L "$BP_STATE/controllers.tsv" ]; then
  regular "$BP_STATE/controllers.tsv" || reject controller_special
fi

set -- "$BP_STATE/accounts.tsv" "$BP_STATE/vouchers.tsv"
[ ! -e "$BP_STATE/credits.tsv" ] || set -- "$@" "$BP_STATE/credits.tsv"
[ ! -e "$BP_STATE/sessions.tsv" ] || set -- "$@" "$BP_STATE/sessions.tsv"
[ "$member_present" -eq 0 ] || set -- "$@" "$BP_STATE/members.tsv" "$BP_STATE/member-events.tsv" "$BP_STATE/member-revision"
[ "$rental_present" -eq 0 ] || set -- "$@" "$BP_STATE/rental-devices.tsv" "$BP_STATE/rental-events.tsv"
[ ! -e "$BP_STATE/controllers.tsv" ] || set -- "$@" "$BP_STATE/controllers.tsv"
for path do complete "$path" || reject partial_record; done
before="$(sha256sum "$@")" || reject source_digest

LC_ALL=C awk -F '\t' '
  function num(v, max) {
    if (v !~ /^(0|[1-9][0-9]*)$/ || length(v)>10) return 0
    return v+0<=max
  }
  NF!=9 || length($1)<2 || length($1)>96 ||
  $1 !~ /^[A-Za-z0-9_.:-]+$/ || ++seen[$1]>1 ||
  !num($2,2147483647) || !num($3,2147483647) ||
  !num($4,2147483647) || $5 !~ /^(0|1)$/ ||
  !num($6,2147483647) {bad=1}
  $9!="" {receipts=1}
  END {if (bad) exit 8; if (receipts) exit 9}
' "$BP_STATE/accounts.tsv" || reject account_corrupt_or_unresolved_receipts

if [ "$member_present" -eq 3 ]; then
  revision="$(cat "$BP_STATE/member-revision")" || reject member_revision
  case "$revision" in 0|[1-9]*) ;; *) reject member_revision;; esac
  case "$revision" in *[!0-9]*) reject member_revision;; esac
  [ "${#revision}" -le 10 ] && [ "$revision" -le 2147483647 ] 2>/dev/null || reject member_revision
  LC_ALL=C awk -F '\t' -v rev="$revision" '
    function num(v, max) {
      if (v !~ /^(0|[1-9][0-9]*)$/ || length(v)>10) return 0
      return v+0<=max
    }
    NF!=11 || length($1)<2 || length($1)>32 ||
    $1 !~ /^[A-Za-z0-9_.-]+$/ || ++seen[$1]>1 ||
    $3 !~ /^(0|1)$/ || !num($7,20000) ||
    !num($8,2147483647) || !num($9,rev) ||
    !num($10,2147483647) {bad=1}
    END {if (bad) exit 8}
  ' "$BP_STATE/members.tsv" || reject member_corrupt_or_out_of_range
  [ ! -s "$BP_STATE/member-events.tsv" ] || reject member_receipts_need_import
fi

if [ "$rental_present" -eq 2 ]; then
  LC_ALL=C awk -F '\t' '
    function num(v) {
      if (v !~ /^(0|[1-9][0-9]*)$/ || length(v)>10) return 0
      return v+0<=2147483647
    }
    NF!=5 || length($1)<2 || length($1)>96 ||
    $1 !~ /^[A-Za-z0-9_.:-]+$/ || ++seen[$1]>1 ||
    $2=="" || !num($3) || !num($5) {bad=1}
    END {if (bad) exit 8}
  ' "$BP_STATE/rental-devices.tsv" || reject rental_corrupt_or_out_of_range
  [ ! -s "$BP_STATE/rental-events.tsv" ] || reject rental_receipts_need_import
fi

if [ -e "$BP_STATE/controllers.tsv" ]; then
  LC_ALL=C awk -F '\t' '
    function uint(v, min, max) {
      if (v !~ /^[0-9]+$/ || length(v)>10) return 0
      return v+0>=min && v+0<=max
    }
    function flag(v) {return v=="0" || v=="1"}
    function pin(v) {return v=="-1" || uint(v,0,63)}
    NF!=15 || length($1)<1 || length($1)>32 ||
    $1 !~ /^[A-Za-z][A-Za-z0-9_.-]*$/ || ++seen[$1]>1 ||
    !flag($2) || !flag($3) || !flag($4) || !flag($5) ||
    !pin($6) || !pin($7) || !pin($8) ||
    !flag($9) || !flag($10) || !flag($11) ||
    !uint($12,1,2000) || !uint($13,10,10000) ||
    !uint($14,1,60) || !uint($15,1,2147483647) {bad=1}
    END {if (bad) exit 8}
  ' "$BP_STATE/controllers.tsv" || reject controller_record_incompatible
fi

after="$(sha256sum "$@")" || reject source_digest
[ "$before" = "$after" ] || reject concurrent_source_change
regular "$BP_STATE/paid-v2-cutover-intent" || reject quiescence_marker_changed
[ ! -e "$BP_STATE/paid-state-uncertain" ] &&
  [ ! -L "$BP_STATE/paid-state-uncertain" ] || reject unresolved_paid_write
sidecars_clear
printf 'V2-MIGRATION-PREFLIGHT READ_ONLY_PASS; paid_ack_authorized=0; migration_authorized=0\n'
