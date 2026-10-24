#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BINDING_T="$ROOT/tools/BlazeRental-Binding-QR.template.html"
BINDING_B="$ROOT/tools/build-binding-qr-tool.py"
PROVISION_T="$ROOT/tools/BlazeRental-QR-Setup.template.html"
PROVISION_B="$ROOT/tools/build-rental-qr-tool.py"
PROVISION_JSON="$ROOT/tools/make-provisioning.py"
Q="$ROOT/ui/vendor/qrcode/qrcode.js"
[ -f "$BINDING_T" ] && [ -f "$BINDING_B" ] && [ -f "$PROVISION_T" ] && [ -f "$PROVISION_B" ] && [ -f "$PROVISION_JSON" ] && [ -f "$Q" ]

# Standard binding QR: existing-install only; never Android enterprise provisioning.
grep -q 'Standard Binding QR' "$BINDING_T"
grep -q '"server_url"' "$BINDING_T"
grep -q '"enrollment_token"' "$BINDING_T"
grep -q '"device_name"' "$BINDING_T"
grep -q '"server_cert_sha256"' "$BINDING_T"
! grep -q 'PROVISIONING_' "$BINDING_T"
! grep -q '__APK_URL__' "$BINDING_T"
! grep -q '__APK_CHECKSUM__' "$BINDING_T"

# Device Owner QR: factory-reset enterprise provisioning from exact signed APK.
grep -q 'Device Owner Provisioning QR' "$PROVISION_T"
grep -q 'PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME' "$PROVISION_T"
grep -q 'PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION' "$PROVISION_T"
grep -q 'PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM' "$PROVISION_T"
grep -q 'PROVISIONING_ADMIN_EXTRAS_BUNDLE' "$PROVISION_T"
! grep -q 'PROVISIONING_SKIP_EDUCATION_SCREENS' "$PROVISION_T"
grep -q 'server_cert_sha256' "$PROVISION_T"
grep -q 'https://192.168.1.1:8443' "$PROVISION_T"
grep -q 'Device Owner provisioning requires an HTTPS BlazePwifi server URL.' "$PROVISION_T"
grep -q 'require_https(a.server_url, "--server-url")' "$PROVISION_JSON"
grep -q 'require_https(a.apk_url, "--apk-url")' "$PROVISION_JSON"
grep -q 'PROVISIONING_WIFI_SSID' "$PROVISION_T"
grep -q '__APK_CHECKSUM__' "$PROVISION_T"
grep -q '__QRCODE_JS__' "$PROVISION_T"
grep -q 'server-cert-sha256' "$PROVISION_JSON"

python3 -m py_compile "$BINDING_B" "$PROVISION_B" "$PROVISION_JSON"
DUMMY_APK="$(mktemp)"
BAD_JSON="$(mktemp)"
printf 'not-an-apk-but-stable-checksum-input' > "$DUMMY_APK"
if python3 "$PROVISION_JSON" --apk "$DUMMY_APK" --apk-url "https://example.invalid/BlazeRental.apk" --server-url "http://192.168.1.1:8080" --enrollment-token "000000000000.000000000000000000000000000000000000" --out "$BAD_JSON" >/dev/null 2>&1; then
  echo "Device Owner provisioning JSON tool accepted insecure HTTP server URL" >&2
  exit 1
fi
if python3 "$PROVISION_JSON" --apk "$DUMMY_APK" --apk-url "http://example.invalid/BlazeRental.apk" --server-url "https://192.168.1.1:8443" --enrollment-token "000000000000.000000000000000000000000000000000000" --out "$BAD_JSON" >/dev/null 2>&1; then
  echo "Device Owner provisioning JSON tool accepted insecure HTTP APK URL" >&2
  exit 1
fi
# HTTPS-only, properly formed Device Owner APK URLs are mandatory for offline QR output.
if python3 "$PROVISION_B" --apk "$DUMMY_APK" --apk-url 'http://example.invalid/BlazeRental.apk' --template "$PROVISION_T" --qrcode-js "$Q" --out "$BAD_JSON" >/dev/null 2>&1; then
  echo "Device Owner HTML QR accepted HTTP APK URL" >&2
  exit 1
fi
if python3 "$PROVISION_B" --apk "$DUMMY_APK" --apk-url 'https://username:password@example.invalid/BlazeRental.apk' --template "$PROVISION_T" --qrcode-js "$Q" --out "$BAD_JSON" >/dev/null 2>&1; then
  echo "Device Owner HTML QR accepted embedded credentials" >&2
  exit 1
fi
if python3 "$PROVISION_B" --apk "$DUMMY_APK" --apk-url 'https:///' --template "$PROVISION_T" --qrcode-js "$Q" --out "$BAD_JSON" >/dev/null 2>&1; then
  echo "Device Owner HTML QR accepted hostname-free URL" >&2
  exit 1
fi
if python3 "$PROVISION_B" --apk "$DUMMY_APK" --apk-url 'https://example.invalid/BlazeRental.apk#fragment' --template "$PROVISION_T" --qrcode-js "$Q" --out "$BAD_JSON" >/dev/null 2>&1; then
  echo "Device Owner HTML QR accepted URL fragment" >&2
  exit 1
fi
if python3 "$PROVISION_JSON" --apk "$DUMMY_APK" --apk-url "https://" --server-url "https://192.168.1.1:8443" --enrollment-token "000000000000.000000000000000000000000000000000000" --out "$BAD_JSON" >/dev/null 2>&1; then
  echo "Provisioning JSON accepted URL with no host" >&2
  exit 1
fi
if python3 "$PROVISION_JSON" --apk "$DUMMY_APK" --apk-url "https://example.invalid/BlazeRental.apk" --server-url "https://admin:password@192.168.1.1:8443" --enrollment-token "000000000000.000000000000000000000000000000000000" --out "$BAD_JSON" >/dev/null 2>&1; then
  echo "Provisioning JSON accepted URL with embedded credentials" >&2
  exit 1
fi
# JS string serialization must not let URL data become HTML structure.
python3 "$PROVISION_B" --apk "$DUMMY_APK" --apk-url 'https://example.invalid/a.apk?ref=<test>&ok=1' --template "$PROVISION_T" --qrcode-js "$Q" --out "$BAD_JSON" >/dev/null
grep -Fq '\u003ctest\u003e' "$BAD_JSON"
grep -Fq '\u0026ok=1' "$BAD_JSON"
rm -f "$DUMMY_APK" "$BAD_JSON"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT INT TERM
python3 "$BINDING_B" --template "$BINDING_T" --qrcode-js "$Q" --out "$TMP" >/dev/null
grep -q 'Standard Binding QR' "$TMP"
! grep -q '__QRCODE_JS__' "$TMP"
! grep -q 'PROVISIONING_' "$TMP"

python3 "$ROOT/tests/test_provisioning_url_ports.py"
python3 "$ROOT/tests/test_rental_qr_branding.py"
# Android WifiConfiguration requires a quoted SSID, and WPA-PSK rejects
# passwords outside 8..63 characters. Execute the page function, not a grep.
node --input-type=commonjs - "$PROVISION_T" <<'JS'
const fs = require("fs");
const html = fs.readFileSync(process.argv[2], "utf8");
const start = html.lastIndexOf("<script>");
const end = html.lastIndexOf("</script>");
if (start < 0 || end < start) throw new Error("provisioning script missing");
const script = html.slice(start + 8, end)
  .replaceAll("__APK_URL__", "https://example.invalid/a.apk")
  .replaceAll("__APK_CHECKSUM__", "abc");
function run(values) {
  const out = {};
  const els = {};
  global.document = {getElementById(id) {
    if (!els[id]) {
      const el = {value: values[id] || ""};
      Object.defineProperty(el, "textContent", {set(v) { out[id] = v; }, get() { return out[id] || ""; }});
      Object.defineProperty(el, "innerHTML", {set(v) { out[id + "_html"] = v; }, get() { return ""; }});
      els[id] = el;
    }
    return els[id];
  }};
  global.qrcode = () => ({addData(s) { out.payload = s; }, make() {}, createSvgTag() { return "<svg/>"; }});
  eval(script);
  generateQr();
  return out;
}
const base = {token:"tok", server:"https://192.168.1.1:8443", name:"Phone", certPin:""};
const empty = run({...base, security:"WPA", ssid:"Cafe WiFi", wifiPass:""});
if (empty.payload || !String(empty.state).includes("8 to 63")) {
  console.error("WPA QR accepted an empty password", empty.state);
  process.exit(1);
}
const short = run({...base, security:"WPA", ssid:"Cafe WiFi", wifiPass:"short"});
if (short.payload) {
  console.error("WPA QR accepted a short password");
  process.exit(1);
}
const ok = run({...base, security:"WPA", ssid:"Cafe WiFi", wifiPass:"correct-horse"});
const payload = JSON.parse(ok.payload);
if (payload["android.app.extra.PROVISIONING_WIFI_SSID"] !== '"Cafe WiFi"') {
  console.error("SSID was not quoted for Android", payload["android.app.extra.PROVISIONING_WIFI_SSID"]);
  process.exit(1);
}
if (payload["android.app.extra.PROVISIONING_WIFI_PASSWORD"] !== "correct-horse") process.exit(1);
const open = run({...base, security:"NONE", ssid:'Room "A"', wifiPass:""});
const openPayload = JSON.parse(open.payload);
if (openPayload["android.app.extra.PROVISIONING_WIFI_SSID"] !== '"Room \\"A\\""') {
  console.error("open SSID quoting failed", openPayload["android.app.extra.PROVISIONING_WIFI_SSID"]);
  process.exit(1);
}
if ("android.app.extra.PROVISIONING_WIFI_PASSWORD" in openPayload) process.exit(1);
JS
echo "BlazeRental split binding / Device Owner QR tool checks passed"
