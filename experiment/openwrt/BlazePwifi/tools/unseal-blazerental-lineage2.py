#!/usr/bin/env python3
import argparse, hashlib, json, pathlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

p=argparse.ArgumentParser()
p.add_argument("--private-key",required=True)
p.add_argument("--wrapped-key",required=True)
p.add_argument("--encrypted-backup",required=True)
p.add_argument("--nonce",required=True)
p.add_argument("--manifest",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()
manifest=json.loads(pathlib.Path(a.manifest).read_text())
priv=serialization.load_pem_private_key(pathlib.Path(a.private_key).read_bytes(),password=None)
key=priv.decrypt(pathlib.Path(a.wrapped_key).read_bytes(),padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
plain=AESGCM(key).decrypt(pathlib.Path(a.nonce).read_bytes(),pathlib.Path(a.encrypted_backup).read_bytes(),manifest["aad"].encode())
actual=hashlib.sha256(plain).hexdigest()
if actual != manifest["backup_plain_sha256"]:
    raise SystemExit("recovered backup checksum mismatch")
pathlib.Path(a.out).write_bytes(plain)
print(a.out)
