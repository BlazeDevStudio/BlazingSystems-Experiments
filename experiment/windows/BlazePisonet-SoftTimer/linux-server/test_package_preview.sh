#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
T="$(mktemp -d)"
case "$T" in /tmp/*) ;; *) echo 'Unexpected disposable test path' >&2; exit 1;; esac
SECURE="$(sudo mktemp -d /root/blaze-lio-preview-test.XXXXXX)"
case "$SECURE" in /root/blaze-lio-preview-test.*) ;; *) echo 'Unexpected root test path' >&2; exit 1;; esac
sudo chmod 0755 "$SECURE"
trap 'sudo rm -r -- "$T" "$SECURE"' EXIT HUP INT TERM
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
sudo sh "$PKG/install-preview.sh" --prefix "$SECURE/installed" --confirm-lab-install >/dev/null
for file in README.md install-preview.sh uninstall-preview.sh blaze_lio_prepare.py blaze_lio_activate.py blaze_lio_status.py blaze_lio_ssh_status.py MANIFEST.sha256; do
  sudo cmp "$PKG/$file" "$SECURE/installed/$file" || {
    echo "FAIL: installed $file differs from checked package" >&2; exit 1;
  }
done
[ "$(sudo stat -c '%u:%a' "$SECURE/installed")" = '0:755' ] || {
  echo 'FAIL: installed code directory has wrong owner or mode' >&2; exit 1;
}
if sudo sh "$PKG/install-preview.sh" --prefix "$SECURE/installed" --confirm-lab-install >/dev/null 2>&1; then
  echo 'FAIL: installer overwrote existing code' >&2; exit 1
fi
cp -R "$PKG" "$T/tampered"
printf '\n# altered\n' >> "$T/tampered/blaze_lio_status.py"
if sudo sh "$T/tampered/install-preview.sh" --prefix "$SECURE/tampered-install" --confirm-lab-install >/dev/null 2>&1; then
  echo 'FAIL: installer admitted a tampered script' >&2; exit 1
fi
sudo test ! -e "$SECURE/tampered-install" || { echo 'FAIL: tamper created install target' >&2; exit 1; }
cp -R "$PKG" "$T/incomplete"
sed -i '/blaze_lio_status.py$/d' "$T/incomplete/MANIFEST.sha256"
if sudo sh "$T/incomplete/install-preview.sh" --prefix "$SECURE/incomplete-install" --confirm-lab-install >/dev/null 2>&1; then
  echo 'FAIL: installer admitted an incomplete manifest' >&2; exit 1
fi
sudo test ! -e "$SECURE/incomplete-install" || { echo 'FAIL: incomplete manifest created install target' >&2; exit 1; }
sudo ln -s "$SECURE/installed" "$SECURE/symlink-install"
if sudo sh "$PKG/install-preview.sh" --prefix "$SECURE/symlink-install" --confirm-lab-install >/dev/null 2>&1; then
  echo 'FAIL: installer followed an existing target symlink' >&2; exit 1
fi
if sudo sh "$PKG/install-preview.sh" --prefix "$T/unconfirmed" >/dev/null 2>&1; then
  echo 'FAIL: installer admitted missing lab confirmation' >&2; exit 1
fi
if sudo sh "$PKG/install-preview.sh" --prefix "$T/unsafe-parent" --confirm-lab-install >/dev/null 2>&1; then
  echo 'FAIL: installer admitted a user-owned parent' >&2; exit 1
fi
if sudo sh "$PKG/uninstall-preview.sh" --prefix "$SECURE/installed" >/dev/null 2>&1; then
  echo 'FAIL: uninstaller admitted missing confirmation' >&2; exit 1
fi
if sudo sh "$PKG/uninstall-preview.sh" --prefix "$SECURE/symlink-install" --confirm-lab-uninstall >/dev/null 2>&1; then
  echo 'FAIL: uninstaller followed a target symlink' >&2; exit 1
fi
sudo sh "$PKG/install-preview.sh" --prefix "$SECURE/changed" --confirm-lab-install >/dev/null
sudo sh -c 'printf "\n# changed\n" >> "$1"' _ "$SECURE/changed/blaze_lio_status.py"
if sudo sh "$PKG/uninstall-preview.sh" --prefix "$SECURE/changed" --confirm-lab-uninstall >/dev/null 2>&1; then
  echo 'FAIL: uninstaller removed changed code' >&2; exit 1
fi
sudo test -e "$SECURE/changed/blaze_lio_status.py" || { echo 'FAIL: changed code was lost' >&2; exit 1; }
sudo sh "$PKG/install-preview.sh" --prefix "$SECURE/extra" --confirm-lab-install >/dev/null
sudo touch "$SECURE/extra/operator-note"
if sudo sh "$PKG/uninstall-preview.sh" --prefix "$SECURE/extra" --confirm-lab-uninstall >/dev/null 2>&1; then
  echo 'FAIL: uninstaller removed unexpected content' >&2; exit 1
fi
sudo test -e "$SECURE/extra/operator-note" || { echo 'FAIL: unexpected content was lost' >&2; exit 1; }
sudo sh "$PKG/uninstall-preview.sh" --prefix "$SECURE/installed" --confirm-lab-uninstall >/dev/null
sudo test ! -e "$SECURE/installed" || { echo 'FAIL: pristine code remains after uninstall' >&2; exit 1; }
sudo test -L "$SECURE/symlink-install" || { echo 'FAIL: unrelated symlink was removed' >&2; exit 1; }
echo 'PisoNet Linux LIO preview package/install/uninstall contract PASS'
