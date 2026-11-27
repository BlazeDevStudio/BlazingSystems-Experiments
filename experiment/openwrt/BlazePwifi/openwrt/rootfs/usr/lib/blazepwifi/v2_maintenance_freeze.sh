#!/bin/sh
# Operator-invoked v1 paid-write freeze. This is not a migration or payment authorization.
set -eu

reject() { printf 'V2-MAINTENANCE-FREEZE REJECT %s; paid_ack_authorized=0; migration_authorized=0\n' "$1" >&2; exit 8; }
regular() { [ -f "$1" ] && [ ! -L "$1" ]; }

[ "$#" -eq 2 ] && [ "$1" = --freeze ] &&
  [ "$2" = --operator-quiesced ] || reject explicit_operator_quiescence_required
BP_STATE=${BP_STATE:-/etc/blazepwifi/state}
BP_RUN=${BP_RUN:-/tmp/blazepwifi}
[ -d "$BP_STATE" ] && [ ! -L "$BP_STATE" ] || reject state_directory
[ -d "$BP_RUN" ] && [ ! -L "$BP_RUN" ] || reject runtime_directory
lock="$BP_RUN/paid-financial.lock"
marker="$BP_STATE/paid-v2-cutover-intent"
regular "$lock" || reject writer_lock

# Use the same inode and lock order as bp_paid_begin/replay_read_lock. A writer
# that started first must finish before the marker can be placed.
exec 6<>"$lock" || reject writer_lock
flock -n 6 || reject writer_busy
[ ! -e "$BP_STATE/paid-state-uncertain" ] &&
  [ ! -L "$BP_STATE/paid-state-uncertain" ] || reject unresolved_paid_write
[ ! -e "$marker" ] && [ ! -L "$marker" ] || reject marker_already_present

# noclobber prevents replacing an existing marker. Once created, any failed
# write or sync leaves it in place so all legacy paid writers remain denied.
umask 077
(set -C; printf 'FROZEN\t%s\n' "$(date +%s)" > "$marker") || reject marker_write
regular "$marker" || reject marker_special
sync || reject marker_sync_uncertain
printf 'V2-MAINTENANCE-FREEZE FROZEN; paid_ack_authorized=0; migration_authorized=0\n'
