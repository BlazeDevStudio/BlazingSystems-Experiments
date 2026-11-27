#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-vendo-seq-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 \
  "$ROOT/tests/v060_vendo_pending_sequence.c" -o "$T/pending-sequence"
"$T/pending-sequence"
python3 "$ROOT/tests/v060_vendo_sequence_contract.py"
