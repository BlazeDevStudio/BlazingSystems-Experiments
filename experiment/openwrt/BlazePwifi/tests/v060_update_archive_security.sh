#!/bin/sh
# SEC-0626: Reject dangerous tar members and ambiguous destinations.
# Synthetic off-device archive tests only. Never use real customer state.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/update.sh"
sh -n "$LIB"
T="$(mktemp -d /tmp/blaze-updater-sec-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
export BP_UPDATE_ROOT="$T/update-state"
export BP_UPDATE_RUN="$T/run"
export BP_UPDATE_TEST_PREFIX="$T/device"
export BP_UPDATE_HEALTH_HOOK=true
. "$LIB"
bp_update_init
TARGET="$T/device/usr/lib/blazepwifi/demo.txt"
GOOD="$T/good"
mkdir -p "$GOOD/payload$(dirname "$TARGET")"
printf 'VERSION=0.5.3-test\nBASE_MIN=0.5.0\nFORMAT=blazepwifi-overlay-v1\n' > "$GOOD/release.env"
printf 'verified synthetic update\n' > "$GOOD/payload$TARGET"
HASH="$(sha256sum "$GOOD/payload$TARGET" | cut -d' ' -f1)"
printf '%s\t644\t%s\n' "$HASH" "$TARGET" > "$GOOD/manifest.tsv"
tar -czf "$T/good.tar.gz" -C "$GOOD" release.env manifest.tsv payload
bp_update_extract_verify "$T/good.tar.gz" "$T/good-extracted"
[ "$(cat "$T/good-extracted/payload$TARGET")" = "verified synthetic update" ]

# These paths match a prefix as strings but escape it when the OS resolves them.
for unsafe in "$TARGET/../out.txt" "$T/device/usr/lib/blazepwifi/../../outside.txt" \
              "$T/device//usr/lib/blazepwifi/demo.txt" "$T/device/./payload"; do
    if bp_update_path_allowed "$unsafe"; then
        echo "unsafe manifest destination accepted" >&2; exit 1
    fi
done
if bp_update_path_allowed 'usr/lib/blazepwifi/file.sh'; then
    echo "nonabsolute manifest destination accepted" >&2; exit 1
fi

refuse() {
    label="$1"; archive="$2"
    if bp_update_extract_verify "$archive" "$T/out-$label" > "$T/reject-$label.log" 2>&1; then
        echo "accepted unsafe archive $label" >&2; exit 1
    fi
    [ ! -e "$T/device/usr/lib/blazepwifi/demo.txt" ] || {
        echo "synthetic target changed during archive inspection" >&2; exit 1
    }
}

# A duplicate tar header can overwrite previously validated content.
tar -czf "$T/duplicate-member.tar.gz" -C "$GOOD" release.env manifest.tsv manifest.tsv payload
refuse duplicate-member "$T/duplicate-member.tar.gz"

# A symlink inside the payload can redirect tar extraction through /etc.
SYMLINK="$T/symlink"
mkdir -p "$SYMLINK/payload$(dirname "$TARGET")"
cp "$GOOD/release.env" "$GOOD/manifest.tsv" "$SYMLINK/"
ln -s /etc/passwd "$SYMLINK/payload$TARGET"
tar -czf "$T/symlink.tar.gz" -C "$SYMLINK" release.env manifest.tsv payload
refuse symlink "$T/symlink.tar.gz"

# Hardlinks can alias other extracted files even without a symlink.
HARDLINK="$T/hardlink"
mkdir -p "$HARDLINK/payload$(dirname "$TARGET")"
cp "$GOOD/release.env" "$GOOD/manifest.tsv" "$HARDLINK/"
cp "$GOOD/payload$TARGET" "$HARDLINK/payload$TARGET"
ln "$HARDLINK/payload$TARGET" "$HARDLINK/payload$(dirname "$TARGET")/alias.txt"
tar -czf "$T/hardlink.tar.gz" -C "$HARDLINK" release.env manifest.tsv payload
refuse hardlink "$T/hardlink.tar.gz"

# Duplicate manifest paths are ambiguous even when each line has valid SHA.
DUP="$T/duplicate-manifest"
mkdir -p "$DUP/payload$(dirname "$TARGET")"
cp "$GOOD/release.env" "$DUP/release.env"
cp "$GOOD/payload$TARGET" "$DUP/payload$TARGET"
cat "$GOOD/manifest.tsv" "$GOOD/manifest.tsv" > "$DUP/manifest.tsv"
tar -czf "$T/duplicate-manifest.tar.gz" -C "$DUP" release.env manifest.tsv payload
refuse duplicate-manifest "$T/duplicate-manifest.tar.gz"

# A syntactically well-formed but path-traversing manifest still fails closed.
TRAVERSAL="$T/traversal-manifest"
mkdir -p "$TRAVERSAL/payload$(dirname "$TARGET")"
cp "$GOOD/release.env" "$TRAVERSAL/release.env"
cp "$GOOD/payload$TARGET" "$TRAVERSAL/payload$TARGET"
printf '%s\t644\t%s\n' "$HASH" "$TARGET/../bad.txt" > "$TRAVERSAL/manifest.tsv"
tar -czf "$T/traversal-manifest.tar.gz" -C "$TRAVERSAL" release.env manifest.tsv payload
refuse traversal-manifest "$T/traversal-manifest.tar.gz"

echo 'SEC-0626 archive security PASS: valid v0.5 archive, duplicate tar entry, symlink, hardlink, duplicate manifest, traversal and no live mutation'
