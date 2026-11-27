#!/usr/bin/env python3
import argparse, base64, hashlib, pathlib

p=argparse.ArgumentParser()
p.add_argument("--apk",required=True)
p.add_argument("--apk-url",required=True)
p.add_argument("--template",required=True)
p.add_argument("--qrcode-js",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()
apk=pathlib.Path(a.apk).read_bytes()
checksum=base64.urlsafe_b64encode(hashlib.sha256(apk).digest()).decode().rstrip("=")
html=pathlib.Path(a.template).read_text(encoding="utf-8")
qr=pathlib.Path(a.qrcode_js).read_text(encoding="utf-8")
html=html.replace("__QRCODE_JS__",qr).replace("__APK_URL__",a.apk_url).replace("__APK_CHECKSUM__",checksum)
pathlib.Path(a.out).write_text(html,encoding="utf-8")
print(a.out)
