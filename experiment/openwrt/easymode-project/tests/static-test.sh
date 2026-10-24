#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
find "$ROOT/core" "$ROOT/modules" "$ROOT/installers" -name '*.sh' -type f -exec sh -n {} \;
# Detection JSON must survive quotes and control bytes from sysinfo.
backup=$(mktemp -d)
if [ -e /tmp/sysinfo ]; then cp -a /tmp/sysinfo "$backup/sysinfo"; fi
rm -rf /tmp/sysinfo
mkdir -p /tmp/sysinfo
printf 'board\t"1"\r' > /tmp/sysinfo/board_name
printf 'Model "X"\nline' > /tmp/sysinfo/model
detect_out=$(sh "$ROOT/core/detect.sh")
rm -rf /tmp/sysinfo
if [ -e "$backup/sysinfo" ]; then mv "$backup/sysinfo" /tmp/sysinfo; fi
rmdir "$backup" 2>/dev/null || rm -rf "$backup"
python3 -c 'import json,sys
j=json.loads(sys.argv[1])
assert j["board"]=="board\t\"1\"\r", j["board"]
assert j["model"]=="Model \"X\"\nline", j["model"]
' "$detect_out"
for f in "$ROOT"/editions/*/manifest.json; do python3 -m json.tool "$f" >/dev/null; done
if command -v node >/dev/null 2>&1; then
  python3 - "$ROOT/installers/offline-html/EasyMode-Installer.html" <<'PY'
import re,sys,pathlib,subprocess,tempfile
s=pathlib.Path(sys.argv[1]).read_text(); m=re.search(r'<script>(.*?)</script>',s,re.S); assert m
p=tempfile.NamedTemporaryFile('w',suffix='.js',delete=False); p.write(m.group(1)); p.close(); subprocess.check_call(['node','--check',p.name])
PY
fi
echo "static tests passed"
