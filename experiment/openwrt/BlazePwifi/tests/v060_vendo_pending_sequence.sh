#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-vendo-seq-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 \
  "$ROOT/tests/v060_vendo_pending_sequence.c" -o "$T/pending-sequence"
"$T/pending-sequence"
# Reject malformed fixed-width flash records before strlen can read past a
# persisted pending-coin structure. ASan makes the regression executable.
cc -std=c11 -Wall -Wextra -Werror -O1 -g -fno-omit-frame-pointer -fsanitize=address \
  "$ROOT/tests/v060_vendo_pending_bounds.c" -o "$T/pending-bounds"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 "$T/pending-bounds"
python3 "$ROOT/tests/v060_vendo_sequence_contract.py"
