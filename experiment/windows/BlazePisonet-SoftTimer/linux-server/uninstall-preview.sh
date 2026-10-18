#!/bin/sh
# Removes only a pristine code-only preview install. No LIO or host configuration.
set -eu
if [ "$#" -ne 3 ] || [ "$1" != '--prefix' ] || [ "$3" != '--confirm-lab-uninstall' ]; then
  echo 'Usage: uninstall-preview.sh --prefix ABSOLUTE_INSTALLED_PATH --confirm-lab-uninstall' >&2
  exit 2
fi
[ "$(id -u)" -eq 0 ] || { echo 'Root is required for a lab code uninstall.' >&2; exit 1; }
PREFIX="$2"
case "$PREFIX" in /*/*) ;; *) echo 'Uninstall prefix must be an absolute child path.' >&2; exit 2;; esac
PARENT="${PREFIX%/*}"
[ -d "$PARENT" ] && [ ! -L "$PARENT" ] &&
  [ "$(realpath -e -- "$PARENT")" = "$PARENT" ] || {
    echo 'Uninstall parent is missing or unsafe.' >&2; exit 1;
  }
CHECK="$PARENT"
while :; do
  MODE="$(stat -c '%u:%a' -- "$CHECK")"
  case "$MODE" in 0:[0-7][0145][0145]) ;; *)
    echo 'Uninstall path has a non-root or writable ancestor.' >&2; exit 1;;
  esac
  [ "$CHECK" = / ] && break
  CHECK="${CHECK%/*}"
  [ -n "$CHECK" ] || CHECK=/
done
[ -d "$PREFIX" ] && [ ! -L "$PREFIX" ] &&
  [ "$(realpath -e -- "$PREFIX")" = "$PREFIX" ] &&
  [ "$(stat -c '%u:%a' -- "$PREFIX")" = '0:755' ] || {
    echo 'Installed code directory is missing or unsafe.' >&2; exit 1;
  }
FILES='README.md install-preview.sh uninstall-preview.sh blaze_lio_prepare.py blaze_lio_activate.py blaze_lio_status.py blaze_lio_ssh_status.py'
for item in "$PREFIX"/* "$PREFIX"/.[!.]* "$PREFIX"/..?*; do
  [ -e "$item" ] || [ -L "$item" ] || continue
  case "${item##*/}" in
    README.md|install-preview.sh|uninstall-preview.sh|blaze_lio_prepare.py|blaze_lio_activate.py|blaze_lio_status.py|blaze_lio_ssh_status.py|MANIFEST.sha256) ;;
    *) echo 'Installed tree has unexpected content; preserving it.' >&2; exit 1;;
  esac
done
for file in $FILES MANIFEST.sha256; do
  case "$file" in *.py|*.sh) mode=755;; *) mode=644;; esac
  [ -f "$PREFIX/$file" ] && [ ! -L "$PREFIX/$file" ] &&
    [ "$(stat -c '%u:%h:%a' -- "$PREFIX/$file")" = "0:1:$mode" ] || {
      echo "Installed file is missing or unsafe: $file" >&2; exit 1;
    }
done
awk -v expected="$FILES" '
  BEGIN { n=split(expected, names, " "); for(i=1;i<=n;i++) wanted[names[i]]=1 }
  NF!=2 || length($1)!=64 || $1 ~ /[^0-9a-f]/ || !($2 in wanted) || seen[$2]++ { bad=1 }
  END { for(i=1;i<=n;i++) if(seen[names[i]]!=1) bad=1; exit bad?1:0 }
' "$PREFIX/MANIFEST.sha256" || {
  echo 'Installed manifest is incomplete or unsafe.' >&2; exit 1;
}
(cd "$PREFIX" && sha256sum -c MANIFEST.sha256 >/dev/null) || {
  echo 'Installed code changed; preserving it.' >&2; exit 1;
}
HOLD="$(mktemp -d "$PARENT/.blaze-lio-uninstall.XXXXXX")"
rmdir -- "$HOLD"
mv -T -n -- "$PREFIX" "$HOLD"
[ ! -e "$PREFIX" ] && [ -d "$HOLD" ] || {
  echo 'Uninstall rename uncertain; inspect both paths.' >&2; exit 1;
}
rm -r -- "$HOLD" || {
  echo "Uninstall removal incomplete; inspect $HOLD" >&2; exit 1;
}
printf 'Removed pristine lab code from %s; LIO, SSH, image and network state unchanged.\n' "$PREFIX"
