#!/usr/bin/env python3
"""Build the Device Owner QR page from the exact APK and an HTTPS APK URL."""
import argparse
import base64
import hashlib
import json
import pathlib
from urllib.parse import urlsplit

p = argparse.ArgumentParser()
p.add_argument("--apk", required=True)
p.add_argument("--apk-url", required=True)
p.add_argument("--template", required=True)
p.add_argument("--qrcode-js", required=True)
p.add_argument("--out", required=True)
a = p.parse_args()

try:
    url = urlsplit(a.apk_url)
    url.port  # Access validates numeric syntax and the allowed port range.
except ValueError:
    p.error("--apk-url must be a valid HTTPS URL")
if (
    url.scheme.lower() != "https"
    or not url.hostname
    or url.username is not None
    or url.password is not None
    or url.fragment
    or any(c.isspace() or ord(c) < 0x20 for c in a.apk_url)
):
    p.error("--apk-url requires HTTPS and a hostname, without credentials or fragment")

apk = pathlib.Path(a.apk).read_bytes()
checksum = base64.urlsafe_b64encode(hashlib.sha256(apk).digest()).decode().rstrip("=")
html = pathlib.Path(a.template).read_text(encoding="utf-8")
qr = pathlib.Path(a.qrcode_js).read_text(encoding="utf-8")
for marker in ("__QRCODE_JS__", "__APK_URL__", "__APK_CHECKSUM__"):
    if marker not in html:
        p.error("provisioning template is missing " + marker)

# Resolve artwork in the template before inserting QR source or URL data.
if "__BLAZE_SYSTEMS_LOGO__" in html:
    logo = pathlib.Path(__file__).with_name("BlazeSystems-Logo-V2.jpg").read_bytes()
    html = html.replace("__BLAZE_SYSTEMS_LOGO__", "data:image/jpeg;base64," + base64.b64encode(logo).decode("ascii"))

# The template places __APK_URL__ inside a JS double-quoted string.
# Escape JSON string syntax AND HTML-significant characters so user-supplied
# URL characters cannot terminate the enclosing script element.
safe_url = json.dumps(a.apk_url, ensure_ascii=True)[1:-1]
safe_url = safe_url.replace("<", r"\u003c").replace(">", r"\u003e").replace("&", r"\u0026")
html = (html.replace("__QRCODE_JS__", qr)
            .replace("__APK_URL__", safe_url)
            .replace("__APK_CHECKSUM__", checksum))
pathlib.Path(a.out).write_text(html, encoding="utf-8")
print(a.out)
