#!/bin/sh
set -eu
set -- ./EasyMode-v7.*-Core-all.ipk
if [ "$#" -eq 1 ] && [ -f "$1" ] && [ -f ./install.sh ] && [ "${EASYMODE_WRAPPER_REENTERED:-0}" != 1 ]; then
 EASYMODE_WRAPPER_REENTERED=1
 export EASYMODE_WRAPPER_REENTERED
 exec sh ./install.sh
fi
echo 'Extract one EasyMode v7 edition offline archive into a separate directory, then run its install.sh.'
echo 'The old v5 scaffold installer is retired; no files were changed.'
exit 1
