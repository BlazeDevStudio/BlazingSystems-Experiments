"""Restore the original private ZIP using the separately retained 32-byte key."""
import argparse,hashlib,json,pathlib,sys
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--key',required=True,type=pathlib.Path)
ap.add_argument('--output',default='R281-OneClick-4.2.3-private.zip',type=pathlib.Path)
ap.add_argument('--library-path',type=pathlib.Path,help='Optional existing Python site-packages/library directory')
args=ap.parse_args()
if args.library_path:sys.path.insert(0,str(args.library_path.resolve()))
try:from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:raise SystemExit('Python package cryptography is required. Use the existing native/lib directory with --library-path on the owner laptop.')
root=pathlib.Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST.json').read_text())
data=(root/manifest['file']).read_bytes();key=args.key.read_bytes()
if len(key)!=32 or data[:8]!=b'R281KIT1':raise SystemExit('Invalid key length or archive format.')
if hashlib.sha256(data).hexdigest()!=manifest['encrypted_sha256']:raise SystemExit('Encrypted archive checksum mismatch.')
try:plain=AESGCM(key).decrypt(data[8:20],data[20:],data[:8])
except Exception:raise SystemExit('Decryption authentication failed. No output written.')
if hashlib.sha256(plain).hexdigest()!=manifest['plaintext_zip_sha256']:raise SystemExit('Restored ZIP checksum mismatch.')
if args.output.exists():raise SystemExit('Output already exists; choose another --output path. Existing files were preserved.')
with args.output.open('xb') as f:f.write(plain)
print('Verified original private ZIP restored: '+str(args.output.resolve()))
