#!/bin/sh
# STORCHK-0674: resolve direct block partitions to their whole-device parent.
# Unsupported/virtual/stacked topology fails closed; this is not media certification.
set -eu
blocked() {
  echo "STORCHK-0674 BLOCKED: $1; no power-cut authorization" >&2
  exit 9
}
[ "$#" -eq 7 ] || blocked 'invalid physical-parent arguments'
SYSFS_ROOT="$1"
SCRATCH="$2"
ROOT="$3"
OVERLAY="$4"
ROM="$5"
BOOT="$6"
ROOT_FS="$7"
[ -d "$SYSFS_ROOT/dev/block" ] || blocked 'sysfs block index unavailable'
SYSFS_ROOT="$(CDPATH= cd -- "$SYSFS_ROOT" 2>/dev/null && pwd -P)" || blocked 'sysfs root cannot be resolved'
is_mm() {
  [ "$1" = "-" ] && return 0
  printf '%s\n' "$1" | awk -F: 'NF==2 && $1 ~ /^[0-9]+$/ && $2 ~ /^[0-9]+$/ { ok=1 } END { exit !ok }'
}
for id in "$SCRATCH" "$ROOT" "$OVERLAY" "$ROM" "$BOOT"; do
  is_mm "$id" || blocked 'invalid major:minor identity'
done
[ "$SCRATCH" != "-" ] || blocked 'scratch mount has no block identity'
[ -n "$ROOT_FS" ] || blocked 'root filesystem type missing'
has_block_relations() {
  # A block device with either slaves or holders participates in a stacked
  # mapping. Its physical ancestry is not a safe standalone scratch identity.
  for relation in slaves holders; do
    [ -d "$1/$relation" ] || continue
    for child in "$1/$relation"/*; do
      [ -e "$child" ] || [ -L "$child" ] || continue
      return 0
    done
  done
  return 1
}
resolve_parent() {
  id="$1"
  require_partition="$2"
  node="$SYSFS_ROOT/dev/block/$id"
  [ -L "$node" ] || return 1
  resolved="$(readlink -f "$node" 2>/dev/null)" || return 1
  case "$resolved" in
    "$SYSFS_ROOT"/devices/virtual/*) return 1 ;;
    "$SYSFS_ROOT"/devices/*/block/*) ;;
    *) return 1 ;;
  esac
  [ -r "$resolved/dev" ] || return 1
  device_mm="$(cat "$resolved/dev" 2>/dev/null)" || return 1
  [ "$device_mm" = "$id" ] || return 1
  if has_block_relations "$resolved"; then return 1; fi
  if [ -f "$resolved/partition" ]; then
    parent="$(dirname "$resolved")"
    case "$parent" in
      "$SYSFS_ROOT"/devices/virtual/*) return 1 ;;
      "$SYSFS_ROOT"/devices/*/block/*) ;;
      *) return 1 ;;
    esac
    [ -r "$parent/dev" ] || return 1
    if has_block_relations "$parent"; then return 1; fi
    parent_mm="$(cat "$parent/dev" 2>/dev/null)" || return 1
    [ "$parent_mm" != "$id" ] || return 1
  else
    [ "$require_partition" = 0 ] || return 1
    parent_mm="$device_mm"
  fi
  is_mm "$parent_mm" || return 1
  printf '%s\n' "$parent_mm"
}
scratch_parent="$(resolve_parent "$SCRATCH" 1)" || blocked 'scratch is not a resolvable direct physical partition'
compare_protected() {
  label="$1"
  id="$2"
  [ "$id" = "-" ] && return 0
  parent_mm="$(resolve_parent "$id" 0)" || blocked "cannot resolve protected $label mount topology"
  [ "$scratch_parent" != "$parent_mm" ] || blocked "scratch shares physical parent with protected $label mount"
}
if [ "$ROOT_FS" = overlay ]; then
  [ "$OVERLAY" != "-" ] || blocked 'overlay root has no separately identified upper storage'
  compare_protected overlay "$OVERLAY"
else
  [ "$ROOT" != "-" ] || blocked 'root mount has no block identity'
  compare_protected root "$ROOT"
  [ "$OVERLAY" = "-" ] || compare_protected overlay "$OVERLAY"
fi
[ "$ROM" = "-" ] || compare_protected rom "$ROM"
[ "$BOOT" = "-" ] || compare_protected boot "$BOOT"
printf '%s\n' 'physical_parent_separation_verified=1'
echo 'STORCHK-0674 PASS: scratch is a direct partition on a different sysfs parent from protected mounts'
