#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
T="$(mktemp -d)"
case "$T" in /tmp/*) ;; *) echo 'Unexpected disposable test path' >&2; exit 1;; esac
trap 'sudo rm -r -- "$T"' EXIT HUP INT TERM
mkdir "$T/one" "$T/two"
sh "$ROOT/build-preview.sh" "$T/one" >/dev/null
sh "$ROOT/build-preview.sh" "$T/two" >/dev/null
NAME='BlazePisonet-LIO-v0.1.0-preview.1-linux'
cmp "$T/one/$NAME.tar.gz" "$T/two/$NAME.tar.gz" || {
  echo 'FAIL: Linux package is not reproducible' >&2; exit 1;
}
(cd "$T/one" && sha256sum -c "$NAME.SHA256SUMS" >/dev/null)
mkdir "$T/unpacked"
tar -xzf "$T/one/$NAME.tar.gz" -C "$T/unpacked"
PKG="$T/unpacked/$NAME"
(cd "$PKG" && sha256sum -c MANIFEST.sha256 >/dev/null)
sudo sh "$PKG/install-preview.sh" --prefix "$T/installed" --confirm-lab-install >/dev/null
for file in README.md install-preview.sh blaze_lio_prepare.py blaze_lio_activate.py blaze_lio_status.py blaze_lio_ssh_status.py MANIFEST.sha256; do
  cmp "$PKG/$file" "$T/installed/$file" || {
    echo "FAIL: installed $file differs from checked package" >&2; exit 1;
  }
done
[ "$(stat -c '%u:%a' "$T/installed")" = '0:755' ] || {
  echo 'FAIL: installed code directory has wrong owner or mode' >&2; exit 1;
}
if sudo sh "$PKG/install-preview.sh" --prefix "$T/installed" --confirm-lab-install >/dev/null 2>&1; then
  echo 'FAIL: installer overwrote existing code' >&2; exit 1
fi
cp -R "$PKG" "$T/tampered"
printf '\n# altered\n' >> "$T/tampered/blaze_lio_status.py"
if sudo sh "$T/tampered/install-preview.sh" --prefix "$T/tampered-install" --confirm-lab-install >/dev/null 2>&1; then
  echo 'FAIL: installer admitted a tampered script' >&2; exit 1
fi
[ ! -e "$T/tampered-install" ] || { echo 'FAIL: tamper created install target' >&2; exit 1; }
cp -R "$PKG" "$T/incomplete"
sed -i '/blaze_lio_status.py$/d' "$T/incomplete/MANIFEST.sha256"
if sudo sh "$T/incomplete/install-preview.sh" --prefix "$T/incomplete-install" --confirm-lab-install >/dev/null 2>&1; then
  echo 'FAIL: installer admitted an incomplete manifest' >&2; exit 1
fi
[ ! -e "$T/incomplete-install" ] || { echo 'FAIL: incomplete manifest created install target' >&2; exit 1; }
ln -s "$T/installed" "$T/symlink-install"
if sudo sh "$PKG/install-preview.sh" --prefix "$T/symlink-install" --confirm-lab-install >/dev/null 2>&1; then
  echo 'FAIL: installer followed an existing target symlink' >&2; exit 1
fi
if sudo sh "$PKG/install-preview.sh" --prefix "$T/unconfirmed" >/dev/null 2>&1; then
  echo 'FAIL: installer admitted missing lab confirmation' >&2; exit 1
fi
echo 'PisoNet Linux LIO preview package/install contract PASS'
