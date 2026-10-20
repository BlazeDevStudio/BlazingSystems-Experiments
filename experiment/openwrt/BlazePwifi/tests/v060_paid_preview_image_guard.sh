#!/bin/sh
# PAY-0774: refuse preview input before downloads or image output.
set -eu
SOURCE="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d "${TMPDIR:-/tmp}/blaze-paid-preview-XXXXXX")"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/build" "$T/dist/v060-native-sdk-lab/x86_64"
cp "$SOURCE/build/build-openwrt-image.sh" "$T/build/build-openwrt-image.sh"
git -C "$T" init -q
git -C "$T" -c user.name=Fixture -c user.email=fixture@example.invalid \
  commit --quiet --allow-empty -m fixture
SHA="$(git -C "$T" rev-parse HEAD)"
B="$T/build/build-openwrt-image.sh"
reject() {
  reason="$1"; shift
  if "$@" >"$T/stdout" 2>"$T/stderr"; then
    echo "PAY-0774 negative unexpectedly passed: $reason" >&2
    exit 1
  fi
  grep -Fq "$reason" "$T/stderr" || {
    echo "PAY-0774 negative returned wrong refusal: $reason" >&2
    cat "$T/stderr" >&2
    exit 1
  }
  [ ! -e "$T/dist/v060-paid-installed-preview" ] || {
    echo 'PAY-0774 refusal created preview output' >&2
    exit 1
  }
}
reject 'requires x86_64 LAB-ONLY CI' env BLAZE_V2_PAID_PREVIEW=lab-only \
  GITHUB_ACTIONS=false RUNNER_TEMP="$T" sh "$B" x86_64
reject 'requires x86_64 LAB-ONLY CI' env BLAZE_V2_PAID_PREVIEW=lab-only \
  GITHUB_ACTIONS=true RUNNER_TEMP="$T" sh "$B" ruijie
reject 'same-run SDK package evidence missing' env BLAZE_V2_PAID_PREVIEW=lab-only \
  GITHUB_ACTIONS=true RUNNER_TEMP="$T" sh "$B" x86_64
printf 'target=x86_64\ncommit=%s\n' "0000000000000000000000000000000000000000" \
  >"$T/dist/v060-native-sdk-lab/x86_64/MANIFEST.txt"
: >"$T/dist/v060-native-sdk-lab/x86_64/SHA256SUMS"
reject "SDK provenance mismatch: commit=$SHA" env BLAZE_V2_PAID_PREVIEW=lab-only \
  GITHUB_ACTIONS=true RUNNER_TEMP="$T" sh "$B" x86_64
printf 'PAY-0774 preview input refusal PASS; no candidate or customer output\n'
