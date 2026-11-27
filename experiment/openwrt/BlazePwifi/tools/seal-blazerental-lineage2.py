#!/usr/bin/env python3
import argparse, base64, hashlib, json, os, pathlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

p=argparse.ArgumentParser()
p.add_argument("--backup",required=True)
p.add_argument("--public-a",required=True)
p.add_argument("--public-b",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()
out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
plain=pathlib.Path(a.backup).read_bytes()
key=os.urandom(32); nonce=os.urandom(12)
aad=b"BlazeRental-v0.5.2-production-lineage2"
cipher=AESGCM(key).encrypt(nonce,plain,aad)
(out/"BlazeRental-v0.5.2-lineage2-signing-backup.enc").write_bytes(cipher)
(out/"BlazeRental-v0.5.2-lineage2-signing-nonce.bin").write_bytes(nonce)
for label,path in [("A",a.public_a),("B",a.public_b)]:
    pub=serialization.load_pem_public_key(pathlib.Path(path).read_bytes())
    wrapped=pub.encrypt(key,padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    (out/f"BlazeRental-v0.5.2-lineage2-key-recovery-{label}.enc").write_bytes(wrapped)
manifest={
 "release":"0.5.2",
 "lineage":"BlazeRental-production-lineage2",
 "payload_cipher":"AES-256-GCM",
 "key_wrap":"RSA-OAEP-SHA256",
 "aad":aad.decode(),
 "backup_plain_sha256":hashlib.sha256(plain).hexdigest(),
 "public_a_sha256":hashlib.sha256(pathlib.Path(a.public_a).read_bytes()).hexdigest(),
 "public_b_sha256":hashlib.sha256(pathlib.Path(a.public_b).read_bytes()).hexdigest(),
 "recovery_paths":["A-private owner-library","B-private owner-offline"]
}
(out/"RECOVERY-MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
