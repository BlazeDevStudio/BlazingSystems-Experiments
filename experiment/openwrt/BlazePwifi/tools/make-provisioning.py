#!/usr/bin/env python3
import argparse, base64, hashlib, json, pathlib

p=argparse.ArgumentParser()
p.add_argument("--apk",required=True)
p.add_argument("--apk-url",required=True)
p.add_argument("--server-url",required=True)
p.add_argument("--enrollment-token",required=True)
p.add_argument("--device-name",default="Rental phone")
p.add_argument("--server-cert-sha256",default="",
               help="optional SHA-256 fingerprint of a self-signed BlazePwifi server certificate")
p.add_argument("--out",required=True)
a=p.parse_args()
pin=a.server_cert_sha256.replace(":","").strip().lower()
if pin and (len(pin) != 64 or any(ch not in "0123456789abcdef" for ch in pin)):
    p.error("--server-cert-sha256 must be a 64-hex SHA-256 fingerprint")
digest=hashlib.sha256(pathlib.Path(a.apk).read_bytes()).digest()
checksum=base64.urlsafe_b64encode(digest).decode().rstrip("=")
data={
 "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME":
   "com.blazesystems.blazerental/.BlazeDeviceAdminReceiver",
 "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION":a.apk_url,
 "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM":checksum,
 "android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE":{
   "server_url":a.server_url,
   "enrollment_token":a.enrollment_token,
   "device_name":a.device_name,
   **({"server_cert_sha256":pin} if pin else {})
 }
}
pathlib.Path(a.out).write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
print(a.out)
