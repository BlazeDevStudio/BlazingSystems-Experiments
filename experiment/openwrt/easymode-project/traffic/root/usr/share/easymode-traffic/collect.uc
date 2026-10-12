import {readfile,writefile,stat,glob,mkdir,chmod} from 'fs';
import {connect} from 'ubus';
import {cursor} from 'uci';
import {settings,command,loadState,saveState,readJSON} from './runtime.uc';
import {advance,uniqueWAN,observeDNS,delta} from './accounting.uc';
import {ensureFlows,parseFlows} from './flows.uc';
let cfg=settings();if(!cfg.enabled)exit(0);
mkdir('/tmp/easymode-traffic',0700);chmod('/tmp/easymode-traffic',0700);
let bus=connect();if(!bus)die('ubus unavailable');
function call(obj,method,args){try{return bus.call(obj,method,args || {}) || {};}catch(e){return {};}}
let old=loadState(),u=cursor(),now=time(),up=int(split(readfile('/proc/uptime') || '0',' ')[0]),boot=trim(readfile('/proc/sys/kernel/random/boot_id') || '');
let all=call('network.interface','dump').interface || [],wan=uniqueWAN(all,cfg.wan,cfg.edition),lans=[];
for(let i in all)if(i.up && i.interface in cfg.lan && i.l3_device)push(lans,i.l3_device);
// Reject layered selected WAN devices rather than count parent + child bytes twice.
let rejected=[];for(let w in wan)for(let other in wan)if(w.device!=other.device && stat('/sys/class/net/'+w.device+'/lower_'+other.device))push(rejected,other.device);
wan=filter(wan,w=>!(w.device in rejected));
for(let w in wan){let base='/sys/class/net/'+w.device;w.rx=int(readfile(base+'/statistics/rx_bytes'));w.tx=int(readfile(base+'/statistics/tx_bytes'));w.identity=trim(readfile(base+'/ifindex') || '');w.bits=64;}
let clients={},identities={},wifi=[];
function client(mac,ip,attrs) {mac=lc(mac || '');if(!match(mac,/^([0-9a-f]{2}:){5}[0-9a-f]{2}$/))return;let d=clients[mac] || {mac,ips:[],online:false,name:''};if(ip && !(ip in d.ips)){push(d.ips,ip);identities[ip]=mac;}clients[mac]={...d,...attrs};}
for(let line in split(readfile('/tmp/dhcp.leases') || '','\n')){let f=split(line,/ +/);if(length(f)>=4)client(f[1],f[2],{name:f[3]=='*'?'':f[3],lease:true});}
let neighbours=[];try{neighbours=json(command('ip -j neigh show 2>/dev/null')) || [];}catch(e){for(let line in split(command('ip neigh show 2>/dev/null'),'\n')){let m=match(line,/^([^ ]+) dev ([^ ]+).* lladdr ([0-9a-f:]+).* (REACHABLE|STALE|DELAY|PROBE)$/);if(m)push(neighbours,{dst:m[1],dev:m[2],lladdr:m[3],state:[m[4]]});}}
for(let n in neighbours)if(n.dev in lans)client(n.lladdr,n.dst,{interface:n.dev,online:('REACHABLE' in (n.state || []) || 'DELAY' in (n.state || []) || 'PROBE' in (n.state || []))});
for(let line in split(command('bridge fdb show 2>/dev/null'),'\n')){let m=match(line,/^([0-9a-f:]+) dev ([A-Za-z0-9_.:@-]+) /);if(m && clients[lc(m[1])] && stat('/sys/class/net/'+m[2]+'/device') && !stat('/sys/class/net/'+m[2]+'/phy80211'))clients[lc(m[1])]={...clients[lc(m[1])],medium:'Ethernet',port:m[2]};}
let radios=call('network.wireless','status');
for(let radio,r in radios)for(let i in r.interfaces || []){if(!match(i.ifname || '',/^[A-Za-z0-9_.:@-]{1,32}$/))continue;let info=call('iwinfo','info',{device:i.ifname}),stations=call('hostapd.'+i.ifname,'get_clients').clients || {},base='/sys/class/net/'+i.ifname,rx=int(readfile(base+'/statistics/rx_bytes')),tx=int(readfile(base+'/statistics/tx_bytes')),previous=null;
 for(let w in old.wifi || [])if(w.interface==i.ifname)previous=w;
 let dt=up-int(old.monotonic || 0),same=old.boot==boot&&dt>0&&dt<=120;
 let w={radio,interface:i.ifname,ssid:i.config?.ssid || info.ssid || '',network:i.config?.network || [],mode:i.config?.mode || '',frequency:info.frequency,channel:info.channel,band:info.frequency?(info.frequency>=5000?'5 GHz':'2.4 GHz'):(r.config?.band=='2g'?'2.4 GHz':r.config?.band=='5g'?'5 GHz':'Unknown band'),width:info.htmode || i.config?.htmode || '',clients:length(keys(stations)),rx,tx,receive_bps:same?delta(previous?.rx,rx,true,64)*8/dt:0,transmit_bps:same?delta(previous?.tx,tx,true,64)*8/dt:0};push(wifi,w);
 for(let mac,s in stations)client(mac,'',{online:s.assoc===true,medium:'WiFi',ssid:w.ssid,radio,band:w.band,interface:i.ifname,signal:s.signal,connected_seconds:s.connected_time,rx_rate:s.rx_rate,tx_rate:s.tx_rate});
}
let offload=u.get('firewall','@defaults[0]','flow_offloading')=='1'||u.get('firewall','@defaults[0]','flow_offloading_hw')=='1',flow=ensureFlows(map(wan,w=>w.device),lans,cfg.limit*4,cfg.devices&&!offload);
let dns={observations:{},bindings:{}};
if(cfg.domains){
 // Reuse OpenWrt's bounded RAM log instead of an unbounded DNS file on tmpfs.
 let lines=split(trim(command('logread -e dnsmasq 2>/dev/null | tail -n 512')),'\n'),last=old.dns?.last_line,index=-1;
 for(let i=0;i<length(lines);i++)if(lines[i]==last)index=i;
 let fresh=old.boot==boot && old.capabilities?.domains?(index>=0?slice(lines,index+1):lines):[];
 dns=observeDNS(old.dns || {},fresh,now,cfg.limit*2);dns.last_line=lines[-1] || '';
}
let mem=readfile('/proc/meminfo') || '',total=int(match(mem,/MemTotal:\s+(\d+)/)?.[1]),available=int(match(mem,/MemAvailable:\s+(\d+)/)?.[1]);
if(total<131072)cfg.interval=max(15,cfg.interval);
let cpu=map(split(trim(split(readfile('/proc/stat') || '','\n')[0]),/ +/),x=>int(x)),cpuTotal=0;for(let n=1;n<min(9,length(cpu));n++)cpuTotal+=cpu[n];let idle=cpu[4]+cpu[5],cpuPercent=null;if(old.system?.cpu_total<cpuTotal && old.boot==boot)cpuPercent=max(0,min(100,100.0*(1.0-(idle-old.system.cpu_idle)/(cpuTotal-old.system.cpu_total+0.0))));
let temperatures=[];for(let p in glob('/sys/class/thermal/thermal_zone*/temp')){let t=int(readfile(p))/1000.0;if(t>0&&t<150)push(temperatures,t);}
let sample={time:now,monotonic:up,boot,wan,wifi,clients:values(clients),flows:parseFlows(flow.data,identities),dns,system:{memory_total_kib:total,memory_available_kib:available,cpu_percent:cpuPercent,cpu_total:cpuTotal,cpu_idle:idle,temperature_c:length(temperatures)?max(...temperatures):null,uptime:up},capabilities:{edition:cfg.edition,wan:length(wan)>0,flow:flow.available,flow_generation:flow.generation,flow_entries_peak:flow.peak || 0,flow_capacity:flow.capacity || 0,flow_limited:flow.limited || false,offload,domains:cfg.domains,wireless:length(wifi)>0,device_accounting:flow.available?'Sampled forwarded flow counters':'Unavailable: enable detailed accounting on a routed, non-offloaded setup',domain_notice:'DNS observations do not prove visits. Encrypted DNS, VPNs, shared IPs and expired flows leave traffic unknown.',flow_notice:'Bounded sampled counters may miss expired or untracked flows. Hardware switch/bridge traffic is not internet usage.',rejected_parent_interfaces:rejected,advanced_classifier:'Not installed; local domain rules only',history_timezone:'UTC'}};
let next=advance(old,sample,cfg);saveState(next,false);bus.disconnect();
