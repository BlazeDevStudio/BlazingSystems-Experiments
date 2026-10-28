#!/usr/bin/env python3
"""Live signed-node revocation and Master outage: localhost only, test credentials only."""
import base64,hashlib,json,os,socket,subprocess,tempfile,time,urllib.request,urllib.error
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[2]
MASTER=ROOT/'ConnectIT-Master-Seed/bin/connectit-master'
SEED=ROOT/'ConnectIT-Seed/bin/connectit-seed'
def port():
 with socket.socket() as s: s.bind(('127.0.0.1',0)); return s.getsockname()[1]
def invoke(*args,env=None):return subprocess.run(list(map(str,args)),text=True,capture_output=True,check=True,env=env)
def start(*args,env=None):return subprocess.Popen(list(map(str,args)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env)
def stop(p):
 if p.poll() is None:p.terminate()
 try:p.wait(timeout=5)
 except subprocess.TimeoutExpired:p.kill();p.wait()
def check(url,p):
 for _ in range(70):
  if p.poll() is not None:raise RuntimeError('server exited '+str(p.returncode))
  try:
   if urllib.request.urlopen(url+'/healthz',timeout=.5).status==200:return
  except Exception:time.sleep(.1)
 raise RuntimeError('healthz timeout')
def b64url(v):return base64.urlsafe_b64encode(v).decode().rstrip('=')
def meshprobe(source,target,node_dir,targetid):
 private=base64.b64decode((node_dir/'node.private.key').read_text())
 cert=(node_dir/'node.cert.json').read_text().strip()
 ts=str(int(time.time()));nonce=b64url(os.urandom(24))
 route='/internal/export?since=0'
 emptyhash=b64url(hashlib.sha256(b'').digest())
 payload=('ConnectIT-mesh-request-v1\nGET\n'+route+'\n'+ts+'\n'+nonce+'\n'+targetid+'\n'+emptyhash).encode()
 signature=b64url(Ed25519PrivateKey.from_private_bytes(private[:32]).sign(payload))
 headers={'X-ConnectIT-Node-Cert':b64url(cert.encode()),'X-ConnectIT-Node-Time':ts,'X-ConnectIT-Node-Nonce':nonce,'X-ConnectIT-Node-Signature':signature}
 request=urllib.request.Request(target+route,headers=headers)
 try:
  with urllib.request.urlopen(request,timeout=4) as r:return r.status
 except urllib.error.HTTPError as e:return e.code
with tempfile.TemporaryDirectory() as temp:
 tmp=Path(temp);master=tmp/'master';a=tmp/'a';b=tmp/'b'
 ma='http://127.0.0.1:'+str(port());ua='http://127.0.0.1:'+str(port());ub='http://127.0.0.1:'+str(port())
 env=os.environ.copy();env['CONNECTIT_BOOTSTRAP_PASSWORD']='test-node-revoke-bootstrap-2026'
 invoke(MASTER,'init','--dir',master,env=env)
 env['CONNECTIT_OLD_ADMIN_PASSWORD']=env['CONNECTIT_BOOTSTRAP_PASSWORD'];env['CONNECTIT_NEW_ADMIN_PASSWORD']='test-node-revoke-rotated-2026'
 invoke(MASTER,'admin-rotate','--dir',master,env=env)
 for directory,name,listen,peer,peerid in [(a,'seed-a',ua,ub,'seed-b'),(b,'seed-b',ub,ua,'seed-a')]:
  invoke(SEED,'init','--dir',directory,'--node-id',name,'--master-public-key',master/'public.key','--listen',listen.replace('http://',''),'--peers',peer,'--peer-ids',peerid,'--revocations-url',ma+'/v1/revocations')
  invoke(MASTER,'node-authorize','--dir',master,'--node-id',name,'--node-public-key',directory/'node.public.key','--node-cert-out',directory/'node.cert.json','--node-ttl-hours',1)
 processes=[]
 try:
  mp=start(MASTER,'start','--dir',master,'--listen',ma.replace('http://',''),env=env);processes.append(mp);check(ma,mp)
  ap=start(SEED,'start','--dir',a,env=env);processes.append(ap);check(ua,ap)
  bp=start(SEED,'start','--dir',b,env=env);processes.append(bp);check(ub,bp)
  before=meshprobe(ua,ub,a,'seed-b')
  assert before==200,('valid signed federation not authorized',before)
  invoke(MASTER,'node-revoke','--dir',master,'--node-cert',a/'node.cert.json')
  stop(bp)
  bp=start(SEED,'start','--dir',b,env=env);processes.append(bp);check(ub,bp)
  after=meshprobe(ua,ub,a,'seed-b')
  assert after==403,('revoked signed Seed accepted',after)
  stop(mp)
  after_offline=meshprobe(ua,ub,a,'seed-b')
  assert after_offline==403,('revoked Seed accepted with Master offline',after_offline)
  assert (b/'signed-node-revocations.json').is_file()
  print(json.dumps({'before_revoke':before,'after_revoke':after,'master_offline_rejection':after_offline,'cached_signed_revoke':True,'localhost_only':True}))
 finally:
  for p in processes:stop(p)
