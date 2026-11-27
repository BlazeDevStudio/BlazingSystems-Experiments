#!/bin/sh
# gallery RED verification
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
G="$ROOT/portal-templates"

[ -f "$G/index.html" ] || { echo "missing portal template gallery" >&2; exit 1; }
[ -f "$G/theme.css" ] || { echo "missing shared preview theme" >&2; exit 1; }
[ -f "$G/README.md" ] || { echo "missing gallery README" >&2; exit 1; }
[ -f "$G/template.json" ] || { echo "missing base template JSON" >&2; exit 1; }

pages="
setup.html
admin-login.html
admin-dashboard.html
portal-home.html
rates.html
insert-coin.html
vendo-select.html
voucher.html
active-session.html
pause-resume.html
vendo-setup.html
controller-setup.html
rental-enrollment.html
rental-locked.html
error-offline.html
"
for p in $pages; do
  [ -f "$G/$p" ] || { echo "missing preview: $p" >&2; exit 1; }
  grep -q 'BlazePwifi Preview' "$G/$p" || { echo "preview marker missing: $p" >&2; exit 1; }
  grep -q 'theme.css' "$G/$p" || { echo "shared theme missing: $p" >&2; exit 1; }
  grep -q "$p" "$G/index.html" || { echo "gallery does not link: $p" >&2; exit 1; }
done

# The first captive viewport must stay simple and action-oriented.
grep -q 'Insert Coin' "$G/portal-home.html"
grep -q 'Use Voucher' "$G/portal-home.html"
grep -q 'Your Time' "$G/portal-home.html"
grep -q 'More device & network details' "$G/portal-home.html"

# Device/network details are below the primary action area and must not expose secrets.
grep -q 'Device IP' "$G/portal-home.html"
grep -q 'Gateway' "$G/portal-home.html"
grep -q 'Connection' "$G/portal-home.html"
! grep -RqiE 'password|secret key|private key|vendo_key|admin_key' "$G" --include='*.html'

# Static previews must not depend on a live router API.
! grep -RqiE 'fetch\(|XMLHttpRequest|/cgi-bin/' "$G" --include='*.html'

echo "BlazePwifi portal template gallery checks passed"
