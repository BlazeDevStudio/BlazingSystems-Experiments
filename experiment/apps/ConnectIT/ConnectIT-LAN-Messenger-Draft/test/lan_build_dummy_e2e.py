#!/usr/bin/env python3
"""Temporary LAN Messenger v0.3.2+15 compatibility DUMMY, not the Flutter binary.

Checks actual ConnectIT Go Master and two Go satellite servers with distinct
Master-enrolled client devices, X25519/HKDF/AES-GCM end-to-end encrypted payloads
and Ed25519/HTTP signed credentials. This deliberately does not claim to execute
LAN Messenger native UI/calling or test physical devices.
"""
import base64
import hashlib
import json
import os
import secrets
import socket
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

REFERENCE_LAN_VERSION = '0.3.2+15'
REFERENCE_LAN_COMMIT = '7d8a08afb39bab8d001fce3d3ba33706e034fcb1'
SCHEME = 'ConnectIT-dummy-e2e-v1'  # explicit domain separation from existing LAN messenger protocol
BASE = Path(__file__).resolve().parents[2]
MASTER_BIN = BASE / 'ConnectIT-Master-Seed/bin/connectit-master'
SEED_BIN = BASE / 'ConnectIT-Seed/bin/connectit-seed'

def b64(v): return base64.b64encode(v).decode('ascii')
def b64u(v): return base64.urlsafe_b64encode(v).decode('ascii').rstrip('=')
def rawpub(k): return k.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
def jbytes(v): return json.dumps(v, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def http(url, payload=None, *, signer=None, cert=None, expected=None):
    method='POST' if payload is not None else 'GET'
    body=jbytes(payload) if payload is not None else b''
    headers = {'Content-Type':'application/json'} if payload is not None else {}
    if signer:
        from urllib.parse import urlsplit
        u=urlsplit(url)
        ts=str(int(time.time()))
        nonce=b64u(secrets.token_bytes(24))
        uri=u.path+('?' + u.query if u.query else '')
        signed='\n'.join([method,u.netloc,uri,ts,nonce,hashlib.sha256(body).hexdigest()]).encode()
        headers.update({'Authorization':'Bearer '+cert,'X-Device-Time':ts,
                        'X-Device-Nonce':nonce,'X-Device-Signature':b64u(signer.sign(signed))})
    req=urllib.request.Request(url,data=body if payload is not None else None,
                               headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=10) as r:
            if expected is not None: assert r.status==expected, (r.status,url)
            return json.load(r)
    except urllib.error.HTTPError as err:
        if expected is not None and err.code==expected:
            return json.loads(err.read())
        raise

def command(args,env=None):
    return subprocess.run(list(map(str,args)),env=env,check=True,text=True,capture_output=True).stdout

def start(args,env=None):
    return subprocess.Popen(list(map(str,args)),env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def healthy(u):
    for _ in range(100):
        try:
            if http(u+'/healthz')['ok']: return
        except Exception: time.sleep(.1)
    raise RuntimeError('endpoint did not become healthy '+u)

class DummyClient:
    def __init__(self,account,password):
        self.id=account
        self.password=password
        self.device=Ed25519PrivateKey.generate() # New registered ConnectIT device, NOT the old LAN X25519 key
        self.local_e2e=X25519PrivateKey.generate() # Ephemeral test fixture trust; no directory or key rotation
        self.cert=None
    def enroll(self,master):
        nonce=b64u(secrets.token_bytes(24))
        packet={'username':self.id,'password':self.password,'device_public_key_b64':b64(rawpub(self.device.public_key())),
                'installation_id':b64u(secrets.token_bytes(24)), 'nonce':nonce,
                'proof_signature_b64':b64u(self.device.sign(f'ConnectIT-enroll-v1\n{self.id}\n{nonce}'.encode()))}
        self.cert=http(master+'/v1/enroll',packet)['device_certificate']
    def key_for(self,other):
        shared=self.local_e2e.exchange(other.local_e2e.public_key())
        pks=sorted([rawpub(self.local_e2e.public_key()),rawpub(other.local_e2e.public_key())])
        info=b'|'.join([SCHEME.encode(), b':'.join(sorted([self.id.encode(),other.id.encode()])), *pks])
        return HKDF(algorithm=hashes.SHA256(),length=32,salt=b'ConnectIT/client-dummy/v1',info=info).derive(shared)
    def encrypt(self,other,plain):
        nonce=secrets.token_bytes(12)
        aad=jbytes({'from':self.id,'to':other.id,'v':SCHEME})
        ciphertext=AESGCM(self.key_for(other)).encrypt(nonce,plain.encode(),aad)
        return b64(jbytes({'v':SCHEME,'n':b64(nonce),'ct':b64(ciphertext)}))
    def decrypt(self,sender,message):
        assert message['from']==sender.id and message['to']==self.id
        obj=json.loads(base64.b64decode(message['ciphertext_b64']))
        assert obj['v']==SCHEME
        aad=jbytes({'from':sender.id,'to':self.id,'v':SCHEME})
        plain=AESGCM(self.key_for(sender)).decrypt(base64.b64decode(obj['n']),base64.b64decode(obj['ct']),aad)
        return plain.decode()
    def send(self,seed,other,text):
        mid=b64u(secrets.token_bytes(18))
        ct=self.encrypt(other,text)
        when=int(time.time())
        envelope={'id':self.id+':'+mid,'from':self.id,'to':other.id,'kind':'message','ciphertext_b64':ct,'created':when}
        packet={'id':mid,'to':other.id,'kind':'message','ciphertext_b64':ct,'created':when,
                'device_signature_b64':b64u(self.device.sign(jbytes(envelope)))}
        return http(seed+'/v1/messages',packet,signer=self.device,cert=self.cert,expected=202),envelope
    def inbox(self,seed,since=0):
        return http(seed+f'/v1/messages?since={since}&wait=0',signer=self.device,cert=self.cert)

def verify_sender(master_pub, envelope):
    parts=envelope['sender_certificate'].split('.')
    Ed25519PublicKey.from_public_bytes(master_pub).verify(
        base64.urlsafe_b64decode(parts[2]+'='*(-len(parts[2])%4)),(parts[0]+'.'+parts[1]).encode())
    claims=json.loads(base64.urlsafe_b64decode(parts[1]+'='*(-len(parts[1])%4)))
    assert claims['sub']==envelope['from'] and claims['exp']>time.time()
    fields={k:envelope[k] for k in ('id','from','to','kind','ciphertext_b64','created')}
    Ed25519PublicKey.from_public_bytes(base64.b64decode(claims['device_public_key'])).verify(
        base64.urlsafe_b64decode(envelope['device_signature_b64']+'='*(-len(envelope['device_signature_b64'])%4)),jbytes(fields))


def main():
    assert MASTER_BIN.is_file() and SEED_BIN.is_file(), 'Build Go binaries first'
    processes=[]
    with tempfile.TemporaryDirectory(prefix='connectit-lan-dummy-') as temp:
        tmp=Path(temp)
        mp,pa,pb=port(),port(),port()
        while len({mp,pa,pb})!=3:mp,pa,pb=port(),port(),port()
        master=f'http://127.0.0.1:{mp}'; seed_a=f'http://127.0.0.1:{pa}'; seed_b=f'http://127.0.0.1:{pb}'
        md,sa,sb=(tmp/s for s in ('master','seed-a','seed-b'))
        env=os.environ.copy();env['CONNECTIT_BOOTSTRAP_PASSWORD']=b64u(secrets.token_bytes(24))
        command([MASTER_BIN,'init','--dir',md],env)
        env['CONNECTIT_OLD_ADMIN_PASSWORD']=env['CONNECTIT_BOOTSTRAP_PASSWORD']
        env['CONNECTIT_NEW_ADMIN_PASSWORD']=b64u(secrets.token_bytes(24))
        command([MASTER_BIN,'admin-rotate','--dir',md],env)
        users=[]
        for nick in ('Alice-Dummy','Bob-Dummy'):
            pw=b64u(secrets.token_bytes(24))
            env['CONNECTIT_PASSWORD']=pw
            command([MASTER_BIN,'account-create','--dir',md,'--nickname',nick],env)
            con=sqlite3.connect(md/'connectit.sqlite3')
            account=con.execute('select id from accounts where nickname=?',(nick,)).fetchone()[0]
            con.close()
            assert len(account)==10 and account.isdigit()
            users.append(DummyClient(account,pw))
        for directory,name,listen,peer in ((sa,'seed-a',pa,pb),(sb,'seed-b',pb,pa)):
            command([SEED_BIN,'init','--dir',directory,'--node-id',name,
                     '--listen',f'127.0.0.1:{listen}','--master-public-key',md/'public.key',
                     '--peers',f'http://127.0.0.1:{peer}'])
        env['CONNECTIT_MESH_SECRET']=b64u(secrets.token_bytes(32))
        try:
            for args in ([MASTER_BIN,'start','--dir',md,'--listen',f'127.0.0.1:{mp}'],
                         [SEED_BIN,'start','--dir',sa],[SEED_BIN,'start','--dir',sb]):
                processes.append(start(args,env))
            for u in (master,seed_a,seed_b): healthy(u)
            alice,bob=users
            alice.enroll(master);bob.enroll(master)
            accepted, sent=alice.send(seed_a,bob,'ConnectIT E2E dummy: hello, Bob')
            assert accepted['id']==sent['id']
            received=None
            for _ in range(100):
                reply=bob.inbox(seed_b)
                messages=[m for m in reply['messages'] if m['id']==sent['id']]
                if messages:
                    received=messages[0]
                    break
                time.sleep(.1)
            assert received is not None, 'Seed-to-Seed delivery failed'
            verify_sender(base64.b64decode((md/'public.key').read_text()),received)
            assert received['hops']==1,received
            assert bob.decrypt(alice,received)=='ConnectIT E2E dummy: hello, Bob'
            assert 'hello, Bob' not in json.dumps(received)
            # Ciphertext tampering MUST fail authentication at the receiver.
            forged=dict(received)
            ciphertext=json.loads(base64.b64decode(forged['ciphertext_b64']))
            raw=bytearray(base64.b64decode(ciphertext['ct']));raw[-1]^=1
            ciphertext['ct']=b64(bytes(raw))
            forged['ciphertext_b64']=b64(jbytes(ciphertext))
            try:
                bob.decrypt(alice,forged)
                raise AssertionError('AES-GCM accepted modified ciphertext')
            except InvalidTag:
                pass
            # Seed must reject a file payload kind outright.
            forged_payload={'id':b64u(secrets.token_bytes(18)),'to':bob.id,
                            'kind':'file-bytes','ciphertext_b64':sent['ciphertext_b64'],
                            'created':int(time.time())}
            signed={'id':alice.id+':'+forged_payload['id'],'from':alice.id,
                    'to':bob.id,'kind':'file-bytes','ciphertext_b64':forged_payload['ciphertext_b64'],
                    'created':forged_payload['created']}
            forged_payload['device_signature_b64']=b64u(alice.device.sign(jbytes(signed)))
            result=http(seed_a+'/v1/messages',forged_payload,signer=alice.device,cert=alice.cert,expected=400)
            assert 'error' in result
            processes[0].terminate();processes[0].wait(timeout=5)
            assert bob.decrypt(alice,[m for m in bob.inbox(seed_b)['messages'] if m['id']==sent['id']][0])=='ConnectIT E2E dummy: hello, Bob'
            print(json.dumps({'dummy_reference_version':REFERENCE_LAN_VERSION,'dummy_reference_commit':REFERENCE_LAN_COMMIT,
              'two_distinct_authoritative_accounts':'PASS','Master_issued_device_credentials':'PASS',
              'X25519_HKDF_AES256GCM_client_E2E':'PASS','recipient_authenticates_sender_signature':'PASS',
              'two_seed_replication_with_one_hop':'PASS','recipient_ciphertext_tamper_detection':'PASS',
              'Seed_refuses_file_payload_kind':'PASS','Master_offline_authenticated_delivery':'PASS',
              'actual_Flutter_APK_or_Windows_binary_test':'NOT_RUN',
              'trust_limitation':'manually provisioned pairwise dummy keys, not production authenticated directory'},indent=2))
        finally:
            for p in processes:
                if p.poll() is None:p.terminate()
            for p in processes:
                try:p.wait(timeout=5)
                except Exception:p.kill()
if __name__=='__main__':main()
