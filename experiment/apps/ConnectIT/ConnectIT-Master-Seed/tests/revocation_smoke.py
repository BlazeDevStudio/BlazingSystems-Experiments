#!/usr/bin/env python3
"""Live localhost proof that revoked Master devices cannot authenticate to a Seed after refreshed signed state."""
import base64, hashlib, json, os, secrets, socket, sqlite3, subprocess, tempfile, time, urllib.error, urllib.request
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ROOT=Path(__file__).resolve().parents[2]
MASTER=ROOT/'ConnectIT-Master-Seed/bin/connectit-master'
SEED=ROOT/'ConnectIT-Seed/bin/connectit-seed'
def u(b):return base64.urlsafe_b64encode(b).decode().rstrip('=')
def b(b):return base64.b64encode(b).decode()
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def cmd(*args,env=None):return subprocess.run(list(map(str,args)),env=env,check=True,capture_output=True,text=True)
def start(*args,env=None):return subprocess.Popen(list(map(str,args)),env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def stop(p):
 if p.poll() is None:p.terminate()
 try:p.wait(timeout=6)
 except subprocess.TimeoutExpired:p.kill();p.wait()
def get(url,cert=None,device=None):
 hdr={}
 if device:
  from urllib.parse import urlsplit
  t=str(int(time.time()));nonce=u(secrets.token_bytes(24));o=urlsplit(url);q=o.path+'?'+o.query if o.query else o.path
  raw='\n'.join(['GET',o.netloc,q,t,nonce,hashlib.sha256(b'').hexdigest()]).encode()
  hdr={'Authorization':'Bearer '+cert,'X-Device-Time':t,'X-Device-Nonce':nonce,'X-Device-Signature':u(device.sign(raw))}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers=hdr),timeout=6) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
def post(url,obj):
 req=urllib.request.Request(url,data=json.dumps(obj).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=6) as r:return json.load(r)
def ready(url):
 for _ in range(60):
  try:
   if get(url+'/healthz')[0]==200:return
  except Exception:time.sleep(.1)
 raise AssertionError(url+' healthz failed')
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp);m=tmp/'m';s=tmp/'s';env=os.environ.copy();env['CONNECTIT_BOOTSTRAP_PASSWORD']=u(secrets.token_bytes(24))
 cmd(MASTER,'init','--dir',m,env=env)
 env['CONNECTIT_OLD_ADMIN_PASSWORD']=env['CONNECTIT_BOOTSTRAP_PASSWORD'];env['CONNECTIT_NEW_ADMIN_PASSWORD']=u(secrets.token_bytes(24))
 cmd(MASTER,'admin-rotate','--dir',m,env=env)
 pw=u(secrets.token_bytes(24));env['CONNECTIT_PASSWORD']=pw
 cmd(MASTER,'account-create','--dir',m,'--nickname','Revocation Smoke',env=env)
 con=sqlite3.connect(m/'connectit.sqlite3');account=con.execute('SELECT id FROM accounts').fetchone()[0];con.close()
 mp,sp=port(),port();base=f'http://127.0.0.1:{mp}';relay=f'http://127.0.0.1:{sp}'
 cmd(SEED,'init','--dir',s,'--node-id','test-seed','--listen',f'127.0.0.1:{sp}','--master-public-key',m/'public.key','--revocations-url',base+'/v1/revocations')
 master=start(MASTER,'start','--dir',m,'--listen',f'127.0.0.1:{mp}',env=env);seed=None
 try:
  ready(base)
  seed=start(SEED,'start','--dir',s,env=env);ready(relay)
  d=Ed25519PrivateKey.generate();key=b(d.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw));n=u(secrets.token_bytes(24))
  cert=post(base+'/v1/enroll',{'username':account,'password':pw,'device_public_key_b64':key,'installation_id':u(secrets.token_bytes(24)),'nonce':n,'proof_signature_b64':u(d.sign(f'ConnectIT-enroll-v1\n{account}\n{n}'.encode()))})['device_certificate']
  code,_=get(relay+'/v1/messages?since=0&wait=0',cert,d);assert code==200,code
  con=sqlite3.connect(m/'connectit.sqlite3');device_id=con.execute('SELECT id FROM devices WHERE account_id=?',(account,)).fetchone()[0];con.close()
  cmd(MASTER,'device-revoke','--dir',m,'--device-id',device_id)
  # The current snapshot is still valid until refreshed. Restart forces authenticated refresh.
  stop(seed);seed=start(SEED,'start','--dir',s,env=env);ready(relay)
  code,data=get(relay+'/v1/messages?since=0&wait=0',cert,d);assert code==401,(code,data)
  stop(master)
  code,data=get(relay+'/v1/messages?since=0&wait=0',cert,d);assert code==401,(code,data)
  print(json.dumps({'master_signed_snapshot':'PASS','revocation_after_seed_refresh':'PASS','revocation_enforced_during_master_outage':'PASS','old_unexpired_certificate_rejected':True,'limitation':'revocation propagation delayed up to refresh interval; cache expires after 1 hour'}))
 finally:
  if seed:stop(seed)
  stop(master)
