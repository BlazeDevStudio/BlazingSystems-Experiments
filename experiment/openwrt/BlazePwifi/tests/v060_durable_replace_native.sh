#!/bin/sh
# FSYNC-0643: compile and test native fsync/rename/parent-dirsync ordering.
# All files are fabricated in /tmp and NEVER touch a real paid ledger.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-v2-atomic-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
command -v cc >/dev/null || { echo 'C compiler required for durability contract tests';exit 1; }
cc -std=c11 -D_GNU_SOURCE -DBLAZE_FIXTURE_ONLY -Wall -Wextra -Werror -O2 \
  "$ROOT/tools/v060_durable_replace.c" -o "$T/native-fixture"
chmod 700 "$T/native-fixture"
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' > "$T/.blaze-v2-fixture-only"
chmod 600 "$T/.blaze-v2-fixture-only"
snap="$T/ledger.tsv"
before="$T/next.tsv"
printf 'old-trusted-fixture\n' > "$snap"
printf 'new-candidate-with-receipt\n' > "$before"
chmod 600 "$snap" "$before"
hash() { sha256sum "$1" | cut -d' ' -f1; }
old="$(hash "$snap")"
new="$(hash "$before")"
[ "$old" != "$new" ]
stage() {
  fault="$1"; expected="$2"
  set +e
  BLAZE_DURABLE_TEST_FAULT="$fault" "$T/native-fixture" "$T" next.tsv ledger.tsv >"$T/result" 2>"$T/error"
  rc=$?
  set -e
  [ "$rc" -eq "$expected" ] || {
    echo "fault $fault reported $rc, wanted $expected" >&2;cat "$T/error" >&2;exit 1;
  }
  ! grep -Fq 'COMMITTED' "$T/result" || {
    echo "fault $fault returned a paid success ACK" >&2;exit 1;
  }
}
stage before-source-fsync 70
[ "$(hash "$snap")" = "$old" ] && [ "$(hash "$before")" = "$new" ]
stage before-rename 71
[ "$(hash "$snap")" = "$old" ] && [ "$(hash "$before")" = "$new" ]
stage after-rename-before-dir-fsync 73
[ "$(hash "$snap")" = "$new" ] && [ ! -e "$before" ]
grep -Fq 'UNCERTAIN' "$T/error"
# After-rename uncertain ACK, retrying must consult stored receipt/highwater.
# This primitive itself does not auto-ACK or replay a paid mutation.
printf 'second-candidate\n' > "$before"
chmod 600 "$before"
out="$("$T/native-fixture" "$T" next.tsv ledger.tsv)"
[ "$out" = COMMITTED ]
[ "$(cat "$snap")" = second-candidate ] && [ ! -e "$before" ]

# A symlink or hardlinked snapshot source cannot be renamed into money store.
printf 'sensitive-untrusted\n' > "$T/maybe.tsv"
chmod 600 "$T/maybe.tsv"
ln -s "$T/maybe.tsv" "$before"
baseline="$(hash "$snap")"
set +e
"$T/native-fixture" "$T" next.tsv ledger.tsv >"$T/result" 2>"$T/error"
rc=$?
set -e
[ "$rc" -ne 0 ] && [ "$(hash "$snap")" = "$baseline" ]
rm "$before"
ln "$T/maybe.tsv" "$before"
set +e
"$T/native-fixture" "$T" next.tsv ledger.tsv >"$T/result" 2>"$T/error"
rc=$?
set -e
[ "$rc" -ne 0 ] && [ "$(hash "$snap")" = "$baseline" ]
rm "$before"
rm "$T/maybe.tsv"

# Never overwrite a destination symlink, even when source is ordinary.
printf 'new-candidate\n' > "$before"
chmod 600 "$before"
mv "$snap" "$T/saved-ledger.tsv"
ln -s "$T/saved-ledger.tsv" "$snap"
set +e
"$T/native-fixture" "$T" next.tsv ledger.tsv >"$T/result" 2>"$T/error"
rc=$?
set -e
[ "$rc" -ne 0 ] && [ "$(cat "$T/saved-ledger.tsv")" = second-candidate ]
rm "$snap"
mv "$T/saved-ledger.tsv" "$snap"

# No directory traversal, foreign state, missing sentinel, or insecure mode.
for candidate in ../bad /etc/passwd .evil ../../ledger; do
  set +e
  "$T/native-fixture" "$T" "$candidate" ledger.tsv >"$T/result" 2>"$T/error"
  rc=$?
  set -e
  [ "$rc" -ne 0 ] && [ "$(hash "$snap")" = "$baseline" ]
done
rm "$T/.blaze-v2-fixture-only"
set +e
"$T/native-fixture" "$T" next.tsv ledger.tsv >"$T/result" 2>"$T/error"
rc=$?
set -e
[ "$rc" -ne 0 ] && [ "$(hash "$snap")" = "$baseline" ]
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' > "$T/.blaze-v2-fixture-only"
chmod 600 "$T/.blaze-v2-fixture-only"
chmod 777 "$T"
set +e
"$T/native-fixture" "$T" next.tsv ledger.tsv >"$T/result" 2>"$T/error"
rc=$?
set -e
[ "$rc" -ne 0 ] && [ "$(hash "$snap")" = "$baseline" ]
chmod 700 "$T"

echo 'FSYNC-0643 PASS: real fsync(file)/renameat/fsync(directory), pre-rename fail keeps old file, post-rename uncertain never ACKs, symlinks/hardlinks/traversal refused'
echo 'NOT PRODUCTION: disposable native Linux fixture ONLY; real OpenWrt filesystems, key-authenticated journal, controller ACK, v1 migration and powercut remain P0'
