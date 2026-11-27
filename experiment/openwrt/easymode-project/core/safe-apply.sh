#!/bin/sh
set -eu
[ "$#" -eq 3 ] || { echo "usage: $0 APPLY_CMD VERIFY_CMD ROLLBACK_CMD" >&2; exit 2; }
APPLY=$1; VERIFY=$2; ROLLBACK=$3
if sh -c "$APPLY" && sh -c "$VERIFY"; then exit 0; fi
sh -c "$ROLLBACK" || true
exit 1
