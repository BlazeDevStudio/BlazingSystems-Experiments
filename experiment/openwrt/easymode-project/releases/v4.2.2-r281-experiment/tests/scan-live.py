"""Read-only scan regression; credentials stay in environment. Run from original workspace."""
import sys,time,json,urllib.request,os
base=os.environ.get('ROUTER_URL','http://192.168.1.1')
def rpc(token,obj,method,args={}):
    body=json.dumps(dict(jsonrpc='2.0',id=1,method='call',params=[token,obj,method,args])).encode()
    with urllib.request.urlopen(urllib.request.Request(base+'/ubus',body,{'Content-Type':'application/json'}),timeout=8) as r: data=json.load(r)
    assert data['result'][0]==0,data
    return data['result'][1]
sid=rpc('0'*32,'session','login',{'username':'root','password':os.environ['ROUTER_PASSWORD']})['ubus_rpc_session']
try:
    start=time.monotonic();r=rpc(sid,'blaze','wifi_scan');assert time.monotonic()-start<3,'Scan blocks the RPC service'
    assert r.get('ok'),r
    for _ in range(70):
        t=time.monotonic();rpc(sid,'blaze','status');assert time.monotonic()-t<3,'Status blocked during scan'
        if not r.get('pending'):break
        time.sleep(1);r=rpc(sid,'blaze','wifi_scan_status',{'id':r['id']})
    assert not r.get('pending'),r
    assert r.get('ok'),r
    assert isinstance(r.get('networks'),list),r
    print(json.dumps({'networks':len(r['networks']),'radios':sorted(set(n['radio'] for n in r['networks'])),'seconds':round(time.monotonic()-start,2),'warnings':r.get('warnings',[])}))
finally:
    try:rpc(sid,'session','destroy')
    except Exception:pass
