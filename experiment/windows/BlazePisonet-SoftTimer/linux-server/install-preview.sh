#!/bin/sh
# Installs code only. No target, sshd, key, network or boot configuration.
set -eu
if [ "$#" -ne 3 ] || [ "$1" != '--prefix' ] || [ "$3" != '--confirm-lab-install' ]; then
  echo 'Usage: install-preview.sh --prefix ABSOLUTE_NEW_PATH --confirm-lab-install' >&2
  exit 2
fi
[ "$(id -u)" -eq 0 ] || { echo 'Root is required for a lab code install.' >&2; exit 1; }
PREFIX="$2"
case "$PREFIX" in
  /*/*) ;;
  *) echo 'Install prefix must be an absolute child of an existing directory.' >&2; exit 2;;
esac
PARENT="${PREFIX%/*}"
[ -d "$PARENT" ] && [ ! -L "$PARENT" ] &&
  [ "$(realpath -e -- "$PARENT")" = "$PARENT" ] || {
    echo 'Install parent is missing or unsafe.' >&2; exit 1;
  }
CHECK="$PARENT"
while :; do
  MODE="$(stat -c '%u:%a' -- "$CHECK")"
  case "$MODE" in 0:[0-7][0145][0145]) ;; *)
    echo 'Install path has a non-root or writable ancestor.' >&2; exit 1;;
  esac
  [ "$CHECK" = / ] && break
  CHECK="${CHECK%/*}"
  [ -n "$CHECK" ] || CHECK=/
done
[ ! -e "$PREFIX" ] && [ ! -L "$PREFIX" ] || {
  echo 'Install target exists; preserving it.' >&2; exit 1;
}
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
FILES='README.md install-preview.sh uninstall-preview.sh blaze_lio_prepare.py blaze_lio_activate.py blaze_lio_status.py blaze_lio_ssh_status.py blaze_lio_configure_ssh_status.py'
[ -f "$ROOT/MANIFEST.sha256" ] && [ ! -L "$ROOT/MANIFEST.sha256" ] || {
  echo 'Package manifest missing or unsafe.' >&2; exit 1;
}
for file in $FILES; do
  [ -f "$ROOT/$file" ] && [ ! -L "$ROOT/$file" ] || {
    echo "Package file missing or unsafe: $file" >&2; exit 1;
  }
done
awk -v expected="$FILES" '
  BEGIN { n=split(expected, names, " "); for(i=1;i<=n;i++) wanted[names[i]]=1 }
  NF!=2 || length($1)!=64 || $1 ~ /[^0-9a-f]/ || !($2 in wanted) || seen[$2]++ { bad=1 }
  END { for(i=1;i<=n;i++) if(seen[names[i]]!=1) bad=1; exit bad?1:0 }
' "$ROOT/MANIFEST.sha256" || {
  echo 'Package manifest is incomplete or unsafe.' >&2; exit 1;
}
(cd "$ROOT" && sha256sum -c MANIFEST.sha256 >/dev/null) || {
  echo 'Package content checksum failed.' >&2; exit 1;
}
STAGE="$(mktemp -d "$PARENT/.blaze-lio-preview.XXXXXX")"
cleanup(){ [ ! -d "$STAGE" ] || rm -r -- "$STAGE"; }
trap cleanup EXIT HUP INT TERM
for file in $FILES; do
  case "$file" in *.py|*.sh) mode=0755;; *) mode=0644;; esac
  install -m "$mode" "$ROOT/$file" "$STAGE/$file"
done
install -m 0644 "$ROOT/MANIFEST.sha256" "$STAGE/MANIFEST.sha256"
chown 0:0 "$STAGE" "$STAGE"/*
chmod 0755 "$STAGE"
mv -T -n -- "$STAGE" "$PREFIX"
[ ! -d "$STAGE" ] || { echo 'Install target raced into existence; preserving it.' >&2; exit 1; }
printf 'Installed lab code at %s; no LIO, SSH, network or boot settings changed.\n' "$PREFIX"
