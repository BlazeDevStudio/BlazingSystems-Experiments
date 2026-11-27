#!/bin/sh
# Separate rental-only edition: inlined Fusion presenter, unchanged payments.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
STANDALONE="$ROOT/profiles/standalone-rental/openwrt"
PAGE="$STANDALONE/rental-standalone.html"
INSTALL="$STANDALONE/install.sh"
[ -s "$PAGE" ] && [ -s "$INSTALL" ]
grep -Fq 'id="blazeStyleStandalone"' "$PAGE"
grep -Fq 'aria-label="Rental console appearance"' "$PAGE"
for mode in fusion compact comfort; do
    grep -Fq "value=\"$mode\"" "$PAGE"
    grep -Fq "data-blaze-style=\"$mode\"" "$PAGE"
done
grep -Fq "blazepwifi.console.appearance.v1" "$PAGE"
grep -Fq "localStorage.setItem(key,style)" "$PAGE"
grep -Fq "localStorage.getItem(key)" "$PAGE"
grep -Fq "const style=allowed.includes(mode)?mode:'fusion'" "$PAGE"
grep -Fq "src=\"/rental/vendor/qrcode.js\"" "$PAGE"
grep -Fq "cp -p \"\$SELF/rental-standalone.html\" \"\$WEB_ROOT/rental/index.html\"" "$INSTALL"
# Do not move Standalone admin to Full's endpoint or remove CSRF handling.
grep -Fq "post('/cgi-bin/blaze-rental-admin'" "$PAGE"
grep -Fq "post('/cgi-bin/blaze-rental-profile'" "$PAGE"
grep -Fq "'X-Blaze-CSRF':csrf" "$PAGE"
grep -Fq "onclick=\"logout()\"" "$PAGE"
! grep -Eq '<script[^>]+(react|alpine|vite|cdn|https?://)' "$PAGE"
! grep -Eq '<link[^>]+(cdn|https?://)' "$PAGE"
sh -n "$INSTALL"
if command -v node >/dev/null 2>&1; then
  TEMP="$(mktemp -d)"
  trap 'rm -rf "$TEMP"' EXIT INT TERM
  sed -n '/^<script>$/,/^<\/script>/p' "$PAGE" | sed '1d;$d' > "$TEMP/rental-ui.js"
  node --check "$TEMP/rental-ui.js"
fi
echo "Standalone Rental BlazeFusion inlined appearance + unchanged secured routes checked"
