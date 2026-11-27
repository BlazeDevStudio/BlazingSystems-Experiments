#!/bin/sh
# UI-only integration: the existing BlazePwifi auth/CSRF and business API stay canonical.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
W="$ROOT/openwrt/rootfs/www/blazepwifi"
HTML="$ROOT/openwrt/rootfs/www/blazepwifi/admin.html"
CSS="$ROOT/openwrt/rootfs/www/blazepwifi/vendor/blazefusion/blaze-fusion.css"
JS="$ROOT/openwrt/rootfs/www/blazepwifi/vendor/blazefusion/blaze-fusion.js"
CORE="$ROOT/openwrt/rootfs/www/blazepwifi/admin/core.js"

[ -s "$HTML" ] && [ -s "$CSS" ] && [ -s "$JS" ] && [ -s "$CORE" ]
grep -Fq 'href="/vendor/blazefusion/blaze-fusion.css"' "$HTML"
grep -Fq 'src="/vendor/blazefusion/blaze-fusion.js"' "$HTML"
grep -Fq 'id="blazeStyleSelect"' "$HTML"
for mode in fusion compact comfort; do
    grep -Fq "value=\"$mode\"" "$HTML"
    grep -Fq "data-blaze-style=\"$mode\"" "$CSS"
done
grep -Fq 'blazepwifi.console.appearance.v1' "$JS"
grep -Fq 'localStorage.setItem' "$JS"
grep -Fq 'localStorage.getItem' "$JS"
grep -Fq '.nav-btn[data-page]' "$JS"
# v0.6 operator UX: search is local-only, dashboard health is driven by
# existing authenticated status responses; no synthetic telemetry or new API.
grep -Fq 'id="blazeNavSearch"' "$HTML"
grep -Fq 'id="blazeNavEmpty"' "$HTML"
grep -Fq 'id="blazeConnection"' "$HTML"
grep -Fq 'id="blazeLastRefresh"' "$HTML"
grep -Fq 'blaze-ops-hero' "$HTML"
grep -Fq 'filterPages()' "$JS"
grep -Fq "event.key.toLowerCase() === 'k'" "$JS"
grep -Fq 'setApplianceState(!!x.ok)' "$CORE"
grep -Fq '#blazeConnection[data-live="no"]' "$CSS"
grep -Fq 'prefers-reduced-motion:reduce' "$CSS"
! grep -Fq 'tailadmin.css">\\n<link' "$HTML"

# The skin must not be a second (unsafe) authenticated business backend.
if grep -Eq '(^|[^[:alnum:]_])(fetch|XMLHttpRequest|eval|Function)\(' "$JS"; then
    echo "BlazeFusion must not contain network/eval logic" >&2
    exit 1
fi
if grep -Eq '@import|url\(https?://|<script[^>]+https?://' "$CSS" "$HTML"; then
    echo "BlazeFusion must remain self-hosted and offline" >&2
    exit 1
fi
# Existing CSRF-bound API and separate Android binding / Device Owner routes.
grep -Fq 'X-Blaze-CSRF' "$CORE"
grep -Fq 'generateBindingQr()' "$HTML"
grep -Fq 'generateProvisioningQr()' "$HTML"
grep -Fq 'id="qrReveal"' "$HTML"
grep -Fq 'qrGeneration++' "$W/admin/rental.js"
grep -Fq 'request!==qrGeneration' "$W/admin/rental.js"
grep -Fq 'One-time token hidden' "$W/admin/rental.js"
grep -Fq "hasPin=typeof pin==='string'" "$W/admin/rental.js"
grep -Fq "Managed QR is missing certificate pin" "$W/admin/rental.js"
grep -Fq '/admin/core.js' "$HTML"
if command -v node >/dev/null 2>&1; then node --check "$JS"; node --check "$W/admin/rental.js"; fi
echo "BlazeFusion presentation-only integration smoke tests passed"
