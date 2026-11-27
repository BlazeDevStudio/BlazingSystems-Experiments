#!/bin/sh
# Opt-in UI preview only; never writes deployed EasyMode or live network configs.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
PROJECT="$(CDPATH= cd -- "$ROOT/../easymode-project" && pwd)"
FUSION="$PROJECT/integrations/blazefusion"
RELEASE="$PROJECT/releases/v4.2.3-r281-experiment/root/www"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM
[ -s "$FUSION/build-preview.py" ]
[ -s "$FUSION/blazefusion.css" ]
[ -s "$FUSION/blazefusion.js" ]
test -s "$RELEASE/index.html"
CHECKSUM="$(sha256sum "$RELEASE/index.html" | awk '{print $1}')"
python3 "$FUSION/build-preview.py" --output "$TMP/www"
[ -s "$TMP/www/index.html" ]
[ -s "$TMP/www/easy/blazefusion/blazefusion.css" ]
[ -s "$TMP/www/easy/blazefusion/blazefusion.js" ]
[ -s "$TMP/www/easy/app.js" ]
grep -Fq 'id="blazefusion-appearance"' "$TMP/www/index.html"
grep -Fq 'src="/easy/app.js?v=4.2.3"' "$TMP/www/index.html"
grep -Fq 'id="logout"' "$TMP/www/index.html"
grep -Fq '/easy/blazefusion/blazefusion.js?v=0.6-preview' "$TMP/www/index.html"
grep -Fq '/easy/blazefusion/blazefusion.css?v=0.6-preview' "$TMP/www/index.html"
for mode in fusion compact comfort; do
    grep -Fq "value=\"$mode\"" "$TMP/www/index.html"
    grep -Fq "data-blaze-style=\"$mode\"" "$FUSION/blazefusion.css"
done
grep -Fq 'blazepwifi.console.appearance.v1' "$FUSION/blazefusion.js"
grep -Fq 'localStorage.setItem' "$FUSION/blazefusion.js"
if grep -Eq '(^|[^a-zA-Z])(fetch|XMLHttpRequest|eval|Function)\(' "$FUSION/blazefusion.js"; then
    echo "Preview must not create a second RPC/backend authority" >&2
    exit 1
fi
if grep -Ei '@import|url\(https?://' "$FUSION/blazefusion.css"; then
    echo "Preview must remain offline/local" >&2
    exit 1
fi
if python3 "$FUSION/build-preview.py" --output "$TMP/www" >"$TMP/rebuild.log" 2>&1; then
    echo "Unsafe preview overwrite was allowed" >&2; exit 1
fi
[ "$(sha256sum "$RELEASE/index.html" | awk '{print $1}')" = "$CHECKSUM" ] || {
    echo "Frozen R281 release was modified" >&2; exit 1
}
python3 -m py_compile "$FUSION/build-preview.py"
if command -v node >/dev/null 2>&1; then node --check "$FUSION/blazefusion.js"; fi
echo "EasyMode Fusion isolated stage + no backend API + source immutability checks passed"
