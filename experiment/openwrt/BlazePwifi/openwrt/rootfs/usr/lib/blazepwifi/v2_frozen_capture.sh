#!/bin/sh
# Operator-only frozen v1 state capture. Never imports money or authorizes v2.
set -eu

reject() { printf 'V2-FROZEN-CAPTURE REJECT %s; paid_ack_authorized=0; migration_authorized=0\n' "$1" >&2; exit 8; }
regular() { [ -f "$1" ] && [ ! -L "$1" ]; }

[ "$#" -eq 2 ] && [ "$1" = --capture ] &&
  [ "$2" = --operator-quiesced ] || reject explicit_operator_quiescence_required

BP_STATE=${BP_STATE:-/etc/blazepwifi/state}
BP_RUN=${BP_RUN:-/tmp/blazepwifi}
BP_SNAPSHOT_ROOT=${BP_SNAPSHOT_ROOT:-}
[ -n "$BP_SNAPSHOT_ROOT" ] || reject operator_snapshot_storage_required
[ -d "$BP_STATE" ] && [ ! -L "$BP_STATE" ] || reject state_directory
[ -d "$BP_RUN" ] && [ ! -L "$BP_RUN" ] || reject runtime_directory
[ -d "$BP_SNAPSHOT_ROOT" ] && [ ! -L "$BP_SNAPSHOT_ROOT" ] || reject snapshot_directory

state_dir="$(CDPATH= cd -P -- "$BP_STATE" && pwd)" || reject state_directory
snapshot_dir="$(CDPATH= cd -P -- "$BP_SNAPSHOT_ROOT" && pwd)" || reject snapshot_directory
case "$snapshot_dir/" in "$state_dir/"*) reject recursive_snapshot_storage;; esac
case "$state_dir/" in "$snapshot_dir/"*) reject state_inside_snapshot_storage;; esac

lock="$BP_RUN/paid-financial.lock"
marker="$state_dir/paid-v2-cutover-intent"
regular "$lock" || reject writer_lock
exec 6<>"$lock" || reject writer_lock
flock -n 6 || reject writer_busy
regular "$marker" || reject frozen_marker_required
[ ! -e "$state_dir/paid-state-uncertain" ] &&
  [ ! -L "$state_dir/paid-state-uncertain" ] || reject unresolved_paid_write

# No special node or symlink may be smuggled into a later restore. Include
# every regular file, including legacy receipts and unknown sidecars.
special="$(find "$state_dir" ! -type f ! -type d -print)" || reject source_scan
[ -z "$special" ] || reject special_source
tmp="$snapshot_dir/.v1-frozen-capture.tmp"
final="$snapshot_dir/v1-frozen-snapshot"
[ ! -e "$tmp" ] && [ ! -L "$tmp" ] || reject incomplete_capture_present
[ ! -e "$final" ] && [ ! -L "$final" ] || reject prior_capture_present

umask 077
mkdir "$tmp" || reject capture_directory
# Compare the original tree to a fresh, private extraction of the staged
# archive. A valid checksum of state.tar alone cannot prove that tar included
# every prepaid balance, receipt, member, lease, or coin sidecar.
before="$(cd "$state_dir" && find . -type f -exec sha256sum {} + | LC_ALL=C sort)" || reject source_digest
before_dirs="$(cd "$state_dir" && find . -type d -print | LC_ALL=C sort)" || reject source_scan
# File bytes alone cannot recover safe permissions, owner IDs or private
# directories. Preserve metadata as part of the capture admission contract.
before_meta="$(cd "$state_dir" && find . \( -type f -o -type d \) -exec stat -c '%a:%u:%g:%n' {} + | LC_ALL=C sort)" || reject source_metadata
tar -cf "$tmp/state.tar" -C "$state_dir" . || reject archive_copy_uncertain
regular "$tmp/state.tar" || reject archive_special
mkdir "$tmp/verification" || reject archive_verify_directory
# GNU/BusyBox tar normally applies the process umask on extraction.
# Unmask permissions ONLY inside the existing private (0700) stage so that
# comparison checks the archive's actual metadata, not our shell umask.
(umask 000; tar -xf "$tmp/state.tar" -C "$tmp/verification") || reject archive_extract_uncertain
archive_special="$(find "$tmp/verification" ! -type f ! -type d -print)" || reject archive_scan
[ -z "$archive_special" ] || reject archive_special_entry
archive_dirs="$(cd "$tmp/verification" && find . -type d -print | LC_ALL=C sort)" || reject archive_scan
[ "$archive_dirs" = "$before_dirs" ] || reject archive_directory_mismatch
archive_files="$(cd "$tmp/verification" && find . -type f -exec sha256sum {} + | LC_ALL=C sort)" || reject archive_digest
[ "$archive_files" = "$before" ] || reject archive_file_mismatch
archive_meta="$(cd "$tmp/verification" && find . \( -type f -o -type d \) -exec stat -c '%a:%u:%g:%n' {} + | LC_ALL=C sort)" || reject archive_metadata
[ "$archive_meta" = "$before_meta" ] || reject archive_metadata_mismatch
rm -rf "$tmp/verification" || reject archive_verify_cleanup
(cd "$tmp" && sha256sum state.tar > SHA256SUMS && sha256sum -c SHA256SUMS >/dev/null) || reject archive_digest
after="$(cd "$state_dir" && find . -type f -exec sha256sum {} + | LC_ALL=C sort)" || reject source_digest
after_dirs="$(cd "$state_dir" && find . -type d -print | LC_ALL=C sort)" || reject source_scan
after_meta="$(cd "$state_dir" && find . \( -type f -o -type d \) -exec stat -c '%a:%u:%g:%n' {} + | LC_ALL=C sort)" || reject source_metadata
[ "$before_meta" = "$after_meta" ] || reject concurrent_source_metadata_change
[ "$after_dirs" = "$before_dirs" ] || reject concurrent_source_directory_change
[ "$before" = "$after" ] || reject concurrent_source_change
special="$(find "$state_dir" ! -type f ! -type d -print)" || reject source_scan
[ -z "$special" ] || reject special_source_changed
regular "$marker" || reject frozen_marker_changed
[ ! -e "$state_dir/paid-state-uncertain" ] &&
  [ ! -L "$state_dir/paid-state-uncertain" ] || reject unresolved_paid_write

# A failed write/sync/rename never gets an ACK. Preserve any incomplete
# capture for operator inspection; a retry must not overwrite it.
sync || reject archive_sync_uncertain
mv "$tmp" "$final" || reject archive_rename_uncertain
sync || reject archive_sync_uncertain
digest="$(sha256sum "$final/state.tar" | awk '{print $1}')" || reject archive_digest
printf 'V2-FROZEN-CAPTURE CAPTURED sha256=%s; paid_ack_authorized=0; migration_authorized=0; physical_durability_verified=0\n' "$digest"
