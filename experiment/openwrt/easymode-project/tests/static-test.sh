#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
find "$ROOT/core" "$ROOT/modules" "$ROOT/installers" -name '*.sh' -type f -exec sh -n {} \;
for f in "$ROOT"/editions/*/manifest.json; do python3 -m json.tool "$f" >/dev/null; done
if command -v node >/dev/null 2>&1; then
  python3 - "$ROOT/installers/offline-html/EasyMode-Installer.html" <<'PY'
import re,sys,pathlib,subprocess,tempfile
s=pathlib.Path(sys.argv[1]).read_text(); m=re.search(r'<script>(.*?)</script>',s,re.S); assert m
p=tempfile.NamedTemporaryFile('w',suffix='.js',delete=False); p.write(m.group(1)); p.close(); subprocess.check_call(['node','--check',p.name])
PY
fi
echo "static tests passed"
