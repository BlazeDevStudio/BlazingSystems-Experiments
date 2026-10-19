import {readfile,writefile,rename} from 'fs';
import {connect} from 'ubus';
import {readjson,exec} from '/usr/share/blaze/common.uc';
import {advance} from '/usr/share/blaze/client-sessions.uc';
let observed={},epoch=time(),up=int(split(readfile('/proc/uptime')||'0',' ')[0]),boot=trim(readfile('/proc/sys/kernel/random/boot_id')||'');
function add(mac,values){mac=lc(mac);if(match(mac,/^([0-9a-f]{2}:){5}[0-9a-f]{2}$/))observed[mac]={...(observed[mac]||{}),mac,...values};}
for(let line in split(trim(readfile('/tmp/dhcp.leases')||''),'\n')){let a=split(line,/ +/);if(length(a)>=4)add(a[1],{ip:a[2],name:a[3]=='*'?'Unnamed':a[3]});}
let neighbors=exec('ip neigh show');if(neighbors.rc)die('Neighbor collection failed');
for(let line in split(neighbors.out,'\n')){
 let m=match(line,/^([^ ]+) dev (br-[^ ]+) lladdr ([0-9a-f:]+) (.*)$/);
 if(m){let prev=observed[lc(m[3])]||{};add(m[3],{ip:prev.ip||m[1],online:!!match(m[4],/\bREACHABLE\b/),medium:'LAN',interface:m[2]});}
}
let c=connect();if(!c)die('Cannot inspect wireless clients');
let objects=exec("ubus list 'hostapd.*'");if(objects.rc)die('Cannot enumerate APs');
for(let obj in split(trim(objects.out),'\n')){
 if(!obj)continue;let r=c.call(obj,'get_clients',{});if(type(r?.clients)!='object')die('Cannot inspect AP clients');
 for(let mac,v in r.clients)if(v.assoc===true)add(mac,{online:true,medium:'Wi-Fi',interface:substr(obj,8)});
}
c.disconnect();
let old=readjson('/tmp/blaze-clients.json',null)||readjson('/etc/blaze/client-sessions.json',{});
let next=advance(old,values(observed),epoch,up,boot);
function atomic(path,data){if(!writefile(path+'.new',data))die('Cannot write session state');if(!rename(path+'.new',path))die('Cannot publish session state');}
if(next.boot!=old.boot||up-int(old.saved_uptime||0)>=1800){next.checkpoint=epoch;next.saved_uptime=up;atomic('/etc/blaze/client-sessions.json',sprintf('%J',next));}
else next.saved_uptime=old.saved_uptime||0;
atomic('/tmp/blaze-clients.json',sprintf('%J',next));
