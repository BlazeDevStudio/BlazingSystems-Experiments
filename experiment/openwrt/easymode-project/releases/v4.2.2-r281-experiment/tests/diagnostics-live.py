import os,json,time,urllib.request
def rpc(sid,obj,method,args={}):
    req=urllib.request.Request(os.environ.get('ROUTER_URL','http://192.168.1.1')+'/ubus',json.dumps({'jsonrpc':'2.0','id':1,'method':'call','params':[sid,obj,method,args]}).encode(),{'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=12) as r:j=json.load(r)
    assert j['result'][0]==0,j
    return j['result'][1] if len(j['result'])>1 else {}
sid=rpc('0'*32,'session','login',{'username':'root','password':os.environ['ROUTER_PASSWORD']})['ubus_rpc_session']
try:
    for kind in ['ping','diagnose','speed']:
        r=rpc(sid,'blaze','nettest_start',{'kind':kind,'source':'sim','target':'1.1.1.1','url':'https://speed.cloudflare.com/__down?bytes=10000000'})
        assert r.get('ok'),r
        for _ in range(70):
            if not r.get('pending'):break
            time.sleep(1);r=rpc(sid,'blaze','nettest_status',{'id':r['id']})
        assert not r.get('pending'),'Worker left test permanently pending'
        assert r.get('ok'),r.get('message')
        print(kind+': '+r['message'],flush=True)
finally:rpc(sid,'session','destroy')
