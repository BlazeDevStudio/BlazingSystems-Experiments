#!/usr/bin/env python3
import argparse, json, pathlib
import qrcode

p=argparse.ArgumentParser()
p.add_argument("--json",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()
data=json.loads(pathlib.Path(a.json).read_text(encoding="utf-8"))
payload=json.dumps(data,separators=(",",":"))
img=qrcode.make(payload)
img.save(a.out)
print(a.out)
