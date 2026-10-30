#!/usr/bin/env bash
# Build Android 16 x86-64 PREVIEW ISO; never publish as production.
set -euo pipefail
[[ $# -eq 2 ]] || { echo "Usage: $0 <source-dir> <artifact-dir>" >&2; exit 2; }
SRC="$(realpath -m -- "$1")"
DEST="$(realpath -m -- "$2")"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PIN="1cd01b9e0dab099693d262e125cd74dccd58e26d"
INSTALLER_PIN="8c6a69fd8d7728ceeddefd42470a488d9785339f"
python3 "$HERE/scripts/check_build.py" --lock "$HERE/foundation.lock.json"
for cmd in repo git python3 xorriso sha256sum; do command -v "$cmd" >/dev/null || { echo "Missing: $cmd" >&2; exit 1; }; done
if [[ -e "$SRC" && ! -d "$SRC/.repo" ]] && [[ -n "$(ls -A "$SRC")" ]]; then
  echo "Refusing to use a nonempty non-repo directory: $SRC" >&2; exit 1
fi
mkdir -p "$SRC" "$DEST"
cd "$SRC"
if [[ ! -d .repo ]]; then
  repo init -u https://github.com/los-tv-x86/lineage_bass_android.git -b lineage-23.2 --git-lfs
fi
git -C .repo/manifests fetch --depth=1 origin "$PIN"
git -C .repo/manifests checkout --detach "$PIN"
[[ "$(git -C .repo/manifests rev-parse HEAD)" == "$PIN" ]] || { echo "Manifest commit mismatch" >&2; exit 1; }
repo sync -c --no-tags --no-clone-bundle -j4
[[ "$(git -C bootable/aaropa rev-parse HEAD)" == "$INSTALLER_PIN" ]] || { echo "Āropa installer mismatch" >&2; exit 1; }
# Install the downstream product as a non-repo source overlay. This is local BlazeDroid
# code, not a renamed upstream product. Repeated builds replace only these tracked files.
[[ ! -L "$SRC/device/blazedroid" ]] || { echo "Refusing symlinked BlazeDroid device directory" >&2; exit 1; }
mkdir -p "$SRC/device/blazedroid"
cp -a -- "$HERE/device/blazedroid/." "$SRC/device/blazedroid/"
repo manifest -r -o "$DEST/resolved-manifest.xml"
(cd "$HERE" && sha256sum device/blazedroid/x86_64/*.mk) > "$DEST/blazedroid-overlay-SHA256SUMS"
export USE_TV_BUILD=false SKIP_AG_DOWNLOADS=false AAROPA_SOURCE=bass
# The upstream environment hook fetches Aaropa and required firmware prebuilts.
source build/envsetup.sh
lunch blazedroid_x86_64-userdebug
m iso_img
mapfile -d '' images < <(find out/target/product/x86_64_tablet -maxdepth 1 -type f -name '*.iso' -print0)
[[ "${#images[@]}" -eq 1 ]] || { echo "Expected exactly one ISO; found ${#images[@]}" >&2; exit 1; }
mapfile -d '' props < <(find out/target/product -type f -name build.prop -print0)
valid=0
for prop in "${props[@]}"; do
  if python3 "$HERE/scripts/check_build.py" --build-prop "$prop" >/dev/null 2>&1; then valid=$((valid+1)); fi
done
[[ "$valid" -ge 1 ]] || { echo "No output build.prop proves Android 16/API 36" >&2; exit 1; }
bash "$HERE/scripts/verify-iso.sh" "${images[0]}"
cp -- "${images[0]}" "$DEST/BlazeDroid-16.0.0-x86_64-PREVIEW.iso"
cd "$DEST"
sha256sum BlazeDroid-16.0.0-x86_64-PREVIEW.iso > SHA256SUMS
echo "PREVIEW ISO built and structurally checked. VM, installation and hardware tests have NOT been done."
