#!/bin/sh
set -eu
if [ -f ./EasyMode-v7.0.0-Core-all.ipk ] && [ -f ./install.sh ]; then
 case "$(readlink -f ./install.sh)" in "$(readlink -f "$0")") ;; *) exec sh ./install.sh ;; esac
fi
echo 'Extract one EasyMode v7 edition offline archive into a separate directory, then run its install.sh.'
echo 'The old v5 scaffold installer is retired; no files were changed.'
exit 1
