#!/usr/bin/env python3
"""Boot a disposable COPY. Never connect to physical routers or publish its credentials."""
import gzip,hashlib,http.server,json,os,pathlib,secrets,shutil,socket,socketserver,struct,subprocess,sys,tempfile,threading,time,urllib.request,zlib
import paramiko,pexpect
BASE=pathlib.Path(__file__).resolve().parents[2];DIST=BASE/'dist-v7';password=secrets.token_urlsafe(24);results=[]
sys.path.insert(0, str(BASE/'traffic/tools'))
from build import VERSION
print('::add-mask::'+password,flush=True)
UEFI='--uefi' in sys.argv
def check(ok,label):
 if not ok:raise AssertionError(label)
 results.append(label);print('PASS:',label,flush=True)
def rpc(method,args=None,token='0'*32,obj='easymode.traffic'):
 body=json.dumps({'jsonrpc':'2.0','id':1,'method':'call','params':[token,obj,method,args or {}]}).encode()
 return json.load(urllib.request.urlopen(urllib.request.Request('http://192.168.77.1/ubus',data=body,headers={'Content-Type':'application/json'}),timeout=12))
class HTTP(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  data=b'T'*1048576;self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def log_message(self,*args):pass
class DNS(socketserver.BaseRequestHandler):
 def handle(self):
  data,sock=self.request;end=12
  while data[end]:end+=data[end]+1
  end+=5;question=data[12:end]
  answer=b'\xc0\x0c'+struct.pack('!HHIH',1,1,30,4)+socket.inet_aton('10.0.2.2')
  sock.sendto(data[:2]+struct.pack('!HHHHH',0x8180,1,1,0,0)+question+answer,self.client_address)
def dns_query(name):
 query=b'\x77\x01'+struct.pack('!HHHHH',0x0100,1,0,0,0)+b''.join(bytes([len(s)])+s.encode() for s in name.split('.'))+b'\0\0\1\0\1'
 with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
  sock.bind(('192.168.77.2',0));sock.settimeout(10);sock.sendto(query,('192.168.77.1',53));return sock.recv(4096)
with tempfile.TemporaryDirectory() as tmp:
 disk=pathlib.Path(tmp)/'disk.img'
 # OpenWrt appends fwtool metadata after the gzip member. Preserve the original
 # release artifact and decompress only its disk member for this disposable VM.
 raw=zlib.decompress((DIST/(f'EasyMode-v{VERSION}-PC-x86_64-'+('UEFI' if UEFI else 'BIOS')+'.img.gz')).read_bytes(),31)
 check(raw[510:512]==b'\x55\xaa' and len(raw)>100*1024*1024,'compressed image has a valid disk member and partition signature')
 disk.write_bytes(raw);del raw
 subprocess.run(['sudo','ip','tuntap','add','dev','emti0','mode','tap','user',str(os.getuid())],check=True)
 subprocess.run(['sudo','ip','addr','add','192.168.77.2/24','dev','emti0'],check=True);subprocess.run(['sudo','ip','link','set','emti0','up'],check=True)
 cmd=['qemu-system-x86_64','-m','256','-smp','2','-nographic','-no-reboot','-drive',f'file={disk},format=raw,if=virtio','-netdev','tap,id=lan,ifname=emti0,script=no,downscript=no','-device','virtio-net-pci,netdev=lan','-netdev','user,id=wan','-device','virtio-net-pci,netdev=wan']
 if UEFI:
  variables=pathlib.Path(tmp)/'OVMF_VARS.fd';shutil.copyfile('/usr/share/OVMF/OVMF_VARS_4M.fd',variables)
  cmd+=['-drive','if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd','-drive',f'if=pflash,format=raw,file={variables}']
 vm=pexpect.spawn(cmd[0],cmd[1:],encoding='utf-8',timeout=180)
 ssh=None
 try:
  vm.expect('Please press Enter to activate this console');vm.sendline('');vm.expect(r'root@[^\r\n]*#')
  # The first console prompt can appear before OpenWrt finishes generating its
  # initial UCI network configuration. Wait for it before changing the VM LAN.
  vm.sendline("for i in $(seq 1 90); do uci -q get network.lan.ipaddr >/dev/null 2>&1 && break; sleep 1; done; if uci -q get network.lan.ipaddr >/dev/null 2>&1; then printf '\\nEASYMODE_NETWORK_READY\\n'; else printf '\\nEASYMODE_NETWORK_MISSING\\n'; cat /etc/config/network; ip -br link; fi")
  vm.expect(r'\r+\nEASYMODE_NETWORK_(READY|MISSING)\r+\n',timeout=120)
  if vm.match.group(1)=='MISSING':raise RuntimeError('VM LAN configuration missing after first-boot wait: '+str(vm.before)[-4000:])
  vm.expect(r'root@[^\r\n]*#')
  # This password exists only in the disposable test copy, never the release image.
  vm.sendline('passwd');vm.expect('[Nn]ew password:');vm.sendline(password);vm.expect('[Rr]etype password:');vm.sendline(password);vm.expect(r'root@[^\r\n]*#')
  vm.sendline("uci set network.lan.ipaddr=192.168.77.1; uci set network.wan=interface; uci set network.wan.device=eth1; uci set network.wan.proto=dhcp; uci commit network; /etc/init.d/network restart")
  vm.expect(r'root@[^\r\n]*#');time.sleep(8)
  ssh=paramiko.SSHClient();ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  for attempt in range(15):
   try:ssh.connect('192.168.77.1',username='root',password=password,timeout=5,look_for_keys=False,allow_agent=False);break
   except (OSError,paramiko.SSHException) as error:
    last_connect_error=error;time.sleep(2)
  else:raise RuntimeError('VM SSH unavailable after network setup: '+str(last_connect_error))
  def run(command):
   i,o,e=ssh.exec_command(command,timeout=90);out=o.read().decode();err=e.read().decode();rc=o.channel.recv_exit_status()
   if rc:raise RuntimeError(f'VM command failed ({rc}): {command}\n{out}\n{err}')
   return out
  check('24.10.8' in run('cat /etc/openwrt_release'),'official OpenWrt 24.10.8 boots')
  for attempt in range(30):
   wan=json.loads(run("ubus call network.interface.wan status 2>/dev/null || echo '{}'"))
   if wan.get('up') and wan.get('l3_device')=='eth1':break
   time.sleep(2)
  else:raise RuntimeError('VM WAN DHCP unavailable: '+json.dumps(wan))
  check(True,'disposable VM has an independent NAT WAN')
  for attempt in range(30):
   try:
    with socket.create_connection(('192.168.77.1',80),timeout=2):break
   except OSError:time.sleep(2)
  else:
   detail=run("/etc/init.d/uhttpd status 2>&1; ls -l /etc/rc.d/*uhttpd 2>&1; logread | tail -30; true")
   raise RuntimeError('VM web API unavailable after first-boot wait:\n'+detail)
  check((rpc('snapshot').get('error',{}).get('code')==-32002 or rpc('snapshot').get('result',[None])[0]==6),'unauthenticated API rejected')
  token=rpc('login',{'username':'root','password':password},obj='session')['result'][1]['ubus_rpc_session']
  def snapshot():return rpc('snapshot',token=token)['result'][1]
  time.sleep(16);s=snapshot();check(s['version']==VERSION and s['fresh'],'supervised collection and authenticated API')
  if UEFI:
   (DIST/'VM-UEFI-TEST-RESULTS.json').write_text(json.dumps({'hardware':'QEMU x86_64 UEFI; NOT PHYSICAL HARDWARE VERIFIED','checks':results},indent=2)+'\n');sys.exit(0)
  check((lambda r:r.get('error',{}).get('code')==-32002 or r.get('result',[None])[0]==6)(rpc('action',{'action':'configure','payload':'{"enabled":false}'})),'unauthenticated mutation rejected')
  invalid=rpc('action',{'action':'configure','payload':'{"wan":["wan;touch /tmp/injected"]}'},token)['result'][1];check(not invalid['ok'] and run('test ! -e /tmp/injected && echo safe').strip()=='safe','input injection rejected')
  check(run("ls -ld /tmp/easymode-traffic/state.json | awk '{print $1}'").strip()=='-rw-------','history file is private')
  # Install real opkg artifacts, then repeat the same install as an upgrade.
  for path in [DIST/f'EasyMode-v{VERSION}-Core-all.ipk',DIST/f'EasyMode-v{VERSION}-Pc-all.ipk']:
   i,o,e=ssh.exec_command('umask 077; cat > /tmp/'+path.name);i.write(path.read_bytes());i.channel.shutdown_write();check(o.channel.recv_exit_status()==0,'package transfer '+path.name)
  run(f'opkg install /tmp/EasyMode-v{VERSION}-Core-all.ipk /tmp/EasyMode-v{VERSION}-Pc-all.ipk');time.sleep(3)
  run(f'opkg install --force-reinstall /tmp/EasyMode-v{VERSION}-Core-all.ipk');time.sleep(3)
  token=rpc('login',{'username':'root','password':password},obj='session')['result'][1]['ubus_rpc_session'];check(snapshot()['config']['edition']=='pc','clean package installation and same-version reinstall preserve edition')
  run("uci set easymode_traffic.main.devices=1; uci set easymode_traffic.main.interval=5; uci commit easymode_traffic; /etc/init.d/easymode-traffic reload");time.sleep(7)
  check(snapshot()['data']['capabilities']['flow'],'bounded nftables observation table created')
  server=socketserver.TCPServer(('127.0.0.1',8889),HTTP);threading.Thread(target=server.serve_forever,daemon=True).start()
  subprocess.run(['sudo','ip','route','add','10.0.2.2/32','via','192.168.77.1','dev','emti0'],check=True)
  before=snapshot();data=urllib.request.urlopen('http://10.0.2.2:8889/traffic',timeout=30).read();check(len(data)==1048576,'real LAN to NAT WAN transfer completed');time.sleep(7)
  after=snapshot();check(any(d.get('download',0)>1000000 for d in after['data']['devices'].values()),'per-device download accounts actual forwarded transfer')
  check(sum(v['download'] for b in after['data']['days'].values() for v in b['wan'].values())>1000000,'WAN download accounts actual forwarded transfer')
  dns_server=socketserver.UDPServer(('127.0.0.1',5353),DNS);threading.Thread(target=dns_server.serve_forever,daemon=True).start()
  run("uci set dhcp.@dnsmasq[0].noresolv=1; uci add_list dhcp.@dnsmasq[0].server='10.0.2.2#5353'; uci commit dhcp")
  enabled=rpc('action',{'action':'configure','payload':'{"domains":true}'},token)['result'][1];check(enabled['ok'],'explicit DNS observation enablement');time.sleep(8)
  check(socket.inet_aton('10.0.2.2') in dns_query('youtube.com'),'controlled client DNS query resolves');time.sleep(6)
  urllib.request.urlopen('http://10.0.2.2:8889/domain',timeout=30).read();time.sleep(6)
  observed=snapshot()['data'];check(observed.get('domains',{}).get('youtube.com',{}).get('download',0)>1000000,'DNS plus real forwarded flow produces labeled domain estimate')
  check(any(b.get('apps',{}).get('YouTube',{}).get('download',0)>1000000 for b in observed['days'].values()),'local service classification uses observed flow estimate')
  rpc('action',{'action':'configure','payload':'{"domains":false}'},token);time.sleep(7)
  check(run("uci -q get dhcp.@dnsmasq[0].logfacility || true").strip()!=' /tmp/easymode-traffic/dns.log'.strip(),'DNS logging restored when disabled');dns_server.shutdown()
  run("uci set firewall.@defaults[0].flow_offloading=1; uci commit firewall; /etc/init.d/firewall reload");time.sleep(7);check(not snapshot()['data']['capabilities']['flow'],'offloading limitation disclosed without disabling acceleration')
  run("uci set firewall.@defaults[0].flow_offloading=0; uci commit firewall; /etc/init.d/firewall reload")
  run("uci set easymode_traffic.main.enabled=0; uci commit easymode_traffic; /etc/init.d/easymode-traffic reload");time.sleep(7);check(not snapshot()['config']['enabled'],'pause persists in UCI');check(run('nft list table inet easymode_traffic >/dev/null 2>&1; test $? != 0; echo removed').strip()=='removed','pause removes observer')
  run("printf broken >/tmp/easymode-traffic/state.json; printf broken >/etc/easymode-traffic/history.json; uci set easymode_traffic.main.enabled=1; uci commit easymode_traffic; /etc/init.d/easymode-traffic restart");time.sleep(7);check(snapshot()['fresh'],'corrupt state recovered and collection resumed')
  subprocess.run(['node','traffic/tests/browser.cjs'],cwd=BASE,env={**os.environ,'VM_PASSWORD':password},check=True)
  check(True,'real browser login, eight views, theme, export, mobile width and logout')
  for edition in ['generic','ap','router','cellular','switch','pc']:
   run('opkg remove easymode-pc easymode-generic easymode-ap easymode-router easymode-cellular easymode-switch 2>/dev/null || true')
   path=DIST/f'EasyMode-v{VERSION}-{edition.title()}-all.ipk';i,o,e=ssh.exec_command('cat > /tmp/edition.ipk');i.write(path.read_bytes());i.channel.shutdown_write();check(o.channel.recv_exit_status()==0,'edition transfer '+edition)
   run('opkg install /tmp/edition.ipk; ucode /usr/share/easymode-traffic/collect.uc')
   current=snapshot();check(current['config']['edition']==edition,'edition installation '+edition)
   if edition in ['ap','switch']:check(not current['data']['wan'],'bridge-only edition does not report invisible WAN: '+edition)
  run('opkg remove easymode-pc easymode-traffic');check(run('test ! -f /usr/libexec/easymode-traffic-worker && echo removed').strip()=='removed','uninstall removes collector')
  server.shutdown()
  print('PASS: virtual integration checks complete',flush=True)
 except Exception:
  if ssh and ssh.get_transport() and ssh.get_transport().is_active():
   try:print('VM diagnostics (synthetic network only):\n'+run('cat /tmp/easymode-traffic/error 2>/dev/null; nft -j list table inet easymode_traffic 2>/dev/null; ubus list easymode.traffic; true')[:10000],flush=True)
   except Exception:pass
  else:print('VM console tail:\n'+str(vm.before)[-4000:],flush=True)
  raise
 finally:
  if ssh:ssh.close()
  vm.close(force=True)
  subprocess.run(['sudo','ip','link','delete','emti0'],check=False)
 (DIST/'VM-TEST-RESULTS.json').write_text(json.dumps({'hardware':'QEMU x86_64 BIOS, 256 MiB; NOT PHYSICAL HARDWARE VERIFIED','checks':results},indent=2)+'\n')
