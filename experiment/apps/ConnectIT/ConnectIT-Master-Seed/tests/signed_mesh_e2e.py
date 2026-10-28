import base64, hashlib, json, os, secrets, sqlite3, subprocess, tempfile, time, urllib.request, urllib.error
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

root=Path(__file__).resolve().parents[2]
master=root/'ConnectIT-Master-Seed/bin/connectit-master'
seed=root/'ConnectIT-Seed/bin/connectit-seed'

def b64(b): return base64.b64encode(b).decode()
def b64u(b): return base64.urlsafe_b64encode(b).decode().rstrip('=')
def request(url, data=None, pkey=None, cert=None):
    method = 'POST' if data is not None else 'GET'
    raw = json.dumps(data,separators=(',',':')).encode() if data is not None else b''
    h={}
    if data is not None:h['Content-Type']='application/json'
    if pkey is not None:
        from urllib.parse import urlsplit
        u=urlsplit(url);stamp=str(int(time.time()));nonce=b64u(secrets.token_bytes(24));urlpath=u.path+('?' + u.query if u.query else '')
        canonical='\n'.join([method,u.netloc,urlpath,stamp,nonce,hashlib.sha256(raw).hexdigest()]).encode()
        h.update({'Authorization':'Bearer '+cert,'X-Device-Time':stamp,'X-Device-Nonce':nonce,'X-Device-Signature':b64u(pkey.sign(canonical))})
    req=urllib.request.Request(url,raw if data is not None else None,headers=h,method=method)
    with urllib.request.urlopen(req,timeout=8) as r:
        return json.load(r)

def start(*argv):return subprocess.Popen(list(map(str,argv)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def wait_health(u):
    for _ in range(50):
        try:return request(u+'/healthz')
        except Exception:time.sleep(.1)
    raise RuntimeError('server not healthy '+u)

with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    mdir=tmp/'master';s1=tmp/'seed-a';s2=tmp/'seed-b'
    os.environ['CONNECTIT_BOOTSTRAP_PASSWORD']='initial-pass-TEST-821419'
    subprocess.run([master,'init','--dir',mdir],check=True,capture_output=True)
    os.environ['CONNECTIT_OLD_ADMIN_PASSWORD']=os.environ['CONNECTIT_BOOTSTRAP_PASSWORD']
    os.environ['CONNECTIT_NEW_ADMIN_PASSWORD']='rotated-pass-TEST-981421'
    subprocess.run([master,'admin-rotate','--dir',mdir],check=True,capture_output=True)
    os.environ['CONNECTIT_PASSWORD']='user-test-password-921824'
    subprocess.run([master,'account-create','--dir',mdir,'--nickname','LocalSmoke'],check=True,capture_output=True)
    con=sqlite3.connect(mdir/'connectit.sqlite3');id=con.execute('select id from accounts').fetchone()[0];con.close()
    assert len(id)==10
    for d,node,port,other in [(s1,'seed-a',8081,8082),(s2,'seed-b',8082,8081)]:
        subprocess.run([seed,'init','--dir',d,'--node-id',node,'--listen',f'127.0.0.1:{port}','--master-public-key',mdir/'public.key','--peers',f'http://127.0.0.1:{other}','--peer-ids',('seed-b' if node=='seed-a' else 'seed-a'),'--revocations-url','http://127.0.0.1:7070/v1/revocations'],check=True,capture_output=True)
    for directory,node in [(s1,'seed-a'),(s2,'seed-b')]:
        subprocess.run([master,'node-authorize','--dir',mdir,'--node-id',node,'--node-public-key',directory/'node.public.key','--node-cert-out',directory/'node.cert.json','--node-ttl-hours','1'],check=True,capture_output=True)
    masterproc=start(master,'start','--dir',mdir,'--listen','127.0.0.1:7070')
    procs=[masterproc]
    wait_health('http://127.0.0.1:7070')
    procs.extend([start(seed,'start','--dir',s1),start(seed,'start','--dir',s2)])
    try:
        for p in ['http://127.0.0.1:7070','http://127.0.0.1:8081','http://127.0.0.1:8082']:wait_health(p)
        key=Ed25519PrivateKey.generate()
        pub=b64(key.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw))
        nonce=b64u(secrets.token_bytes(24));install=b64u(secrets.token_bytes(24))
        enrollment={'username':id,'password':os.environ['CONNECTIT_PASSWORD'],'device_public_key_b64':pub,'installation_id':install,'nonce':nonce,'proof_signature_b64':b64u(key.sign(f'ConnectIT-enroll-v1\n{id}\n{nonce}'.encode()))}
        cert=request('http://127.0.0.1:7070/v1/enroll',enrollment)['device_certificate']
        mid=b64u(secrets.token_bytes(16))
        ciphertext=b64(secrets.token_bytes(32)) # opaque dummy test bytes, not a claim of client-side E2E encryption.
        now=int(time.time())
        envelope={'id':id+':'+mid,'from':id,'to':id,'kind':'message','ciphertext_b64':ciphertext,'created':now}
        dsig=b64u(key.sign(json.dumps(envelope,separators=(',',':')).encode()))
        sent={'id':mid,'to':id,'kind':'message','ciphertext_b64':ciphertext,'created':now,'device_signature_b64':dsig}
        request('http://127.0.0.1:8081/v1/messages',sent,key,cert)
        msg=None
        for i in range(70):
            v=request('http://127.0.0.1:8082/v1/messages?since=0&wait=0',None,key,cert)
            if any(m['id']==envelope['id'] for m in v['messages']):msg=v;break
            time.sleep(.1)
        assert msg,'message not replicated to peer'
        assert msg['messages'][0]['hops']==1, msg['messages'][0]
        # Bounded light-workload resource observation: 200 signed 256-byte messages.
        for n in range(200):
            another=b64u(secrets.token_bytes(16));ct=b64(secrets.token_bytes(256));when=int(time.time())
            content={'id':id+':'+another,'from':id,'to':id,'kind':'message','ciphertext_b64':ct,'created':when}
            sign=b64u(key.sign(json.dumps(content,separators=(',',':')).encode()))
            request('http://127.0.0.1:8081/v1/messages',{'id':another,'to':id,'kind':'message','ciphertext_b64':ct,'created':when,'device_signature_b64':sign},key,cert)
        time.sleep(4) # allow a peer sync pass
        rss={}
        for label,p in [('seed_a',procs[1]),('seed_b',procs[2])]:
            raw=Path(f'/proc/{p.pid}/status').read_text()
            line=next(x for x in raw.splitlines() if x.startswith('VmRSS:'))
            rss[label]=int(line.split()[1])
        print(json.dumps({'workload':'201 signed messages, 1 original and 200 x 256-byte opaque payloads, 2 local seeds',
                          'seed_a_rss_kib':rss['seed_a'],'seed_b_rss_kib':rss['seed_b'],
                          'note':'Linux x86-64 process RSS after a light test; not proof of sustained 1 GB hardware performance'}))
        procs[0].terminate();procs[0].wait(timeout=5)
        v=request('http://127.0.0.1:8082/v1/messages?since=0&wait=0',None,key,cert)
        assert any(m['id']==envelope['id'] for m in v['messages'])
        print(json.dumps({'ten_digit_id':'PASS','first_device_signed_enrollment':'PASS','seed_one_to_seed_two_signed_replication':'PASS','mesh_auth':'Master-signed Ed25519, no shared secret','hop_count':1,'master_offline_verified_delivery':'PASS','client_side_E2E_encryption':'NOT_IMPLEMENTED_IN_SMOKE'}))
    finally:
        for p in procs:
            if p.poll() is None:p.terminate()
        for p in procs:
            try:p.wait(timeout=5)
            except Exception:p.kill()
