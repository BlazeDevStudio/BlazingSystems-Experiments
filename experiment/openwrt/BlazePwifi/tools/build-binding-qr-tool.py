#!/usr/bin/env python3
import argparse, base64, pathlib

p=argparse.ArgumentParser()
p.add_argument("--template",required=True)
p.add_argument("--qrcode-js",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()
html=pathlib.Path(a.template).read_text(encoding="utf-8")
qr=pathlib.Path(a.qrcode_js).read_text(encoding="utf-8")
if "__QRCODE_JS__" not in html:
    p.error("binding template is missing __QRCODE_JS__")
if "__BLAZE_SYSTEMS_LOGO__" in html:
    logo=pathlib.Path(__file__).with_name("BlazeSystems-Logo-V2.jpg").read_bytes()
    html=html.replace("__BLAZE_SYSTEMS_LOGO__","data:image/jpeg;base64,"+base64.b64encode(logo).decode("ascii"))
html=html.replace("__QRCODE_JS__",qr)
pathlib.Path(a.out).write_text(html,encoding="utf-8")
print(a.out)
