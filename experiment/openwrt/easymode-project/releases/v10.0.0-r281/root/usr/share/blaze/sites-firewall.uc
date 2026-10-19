import {glob,readfile,writefile,unlink,popen} from 'fs';
import {profile} from '/usr/share/blaze/sites.uc';
let p=profile(json(readfile('/etc/blaze/sites.json')||'{"enabled":false,"mode":"off","domains":[],"devices":[]}'));
function run(cmd){let f=popen(cmd+' 2>&1','r'),s=f.read('all'),rc=f.close();if(rc)die(s);return s;}
if(!p.enabled){run('nft delete table inet blaze_sites 2>/dev/null || true');run('nft delete table bridge blaze_sites 2>/dev/null || true');exit(0);}
if(trim(run("uci -q get firewall.@defaults[0].flow_offloading || true"))=='1')die('Disable flow offloading in Advanced before enabling filtering.');
let names={};for(let f in [...glob('/sys/class/net/br-*/brif/*'),...glob('/sys/class/net/br-*')]){let n=split(f,'/');n=n[length(n)-1];if(match(n,/^[A-Za-z0-9_.:-]+$/))names[n]=true;}
let devs=keys(names);if(!length(devs))die('No client bridges found.');let interfaces='{ '+join(', ',map(devs,n=>'"'+n+'"'))+' }';
let local4=trim(run("ubus call network.interface.lan status | jsonfilter -e '@[\"ipv4-address\"][0].address'")),local6='';
if(!match(local4,/^[0-9.]+$/))die('LAN management address unavailable.');
for(let line in split(readfile('/proc/net/if_inet6')||'','\n')){let cols=split(trim(line),/\s+/);if(cols[5]=='br-lan'&&cols[3]=='00'&&match(cols[0],/^[0-9a-f]{32}$/)){let groups=[];for(let i=0;i<32;i+=4)push(groups,substr(cols[0],i,4));local6=join(':',groups);break;}}
let text='';for(let family in ['inet','bridge'])text+='add table '+family+' blaze_sites\ndelete table '+family+' blaze_sites\nadd table '+family+' blaze_sites\n';
text+='add chain bridge blaze_sites pre { type filter hook prerouting priority -300; policy accept; }\n';
text+='add chain inet blaze_sites dns { type nat hook prerouting priority -101; policy accept; }\n';
text+='add chain inet blaze_sites guard { type filter hook input priority -10; policy accept; }\n';
text+='add rule inet blaze_sites guard iifname "lo" return\n';
// Old DNS conntrack entries must never select another device's policy after edits.
for(let i=0;i<32;i++){
 let port=1054+i,d=p.devices[i];
 text+='add rule inet blaze_sites guard meta l4proto { tcp, udp } th dport '+port+(d?' ether saddr != '+d.mac:'')+' drop\n';
}
for(let d in p.devices)text+='add rule inet blaze_sites guard ether saddr '+d.mac+' meta l4proto { tcp, udp } th dport 1053 drop\n';
text+='add rule inet blaze_sites guard iifname '+interfaces+' ct status dnat meta l4proto { tcp, udp } th dport 1053-1085 return\n';
text+='add rule inet blaze_sites guard meta l4proto { tcp, udp } th dport 1053-1085 drop\n';
function add(v,port,match){
 if(v.mode=='off'){for(let family in ['inet','bridge'])text+='add rule '+family+' blaze_sites '+(family=='inet'?'dns':'pre')+' '+match+' return\n';return;}
 text+='add rule bridge blaze_sites pre iifname '+interfaces+' '+match+' meta l4proto { tcp, udp } th dport 53 counter meta pkttype set unicast meta broute set 1\n';
 // Bridge slave ports have no local IP: redirect-to-port would silently drop.
 text+='add rule inet blaze_sites dns iifname '+interfaces+' '+match+' meta nfproto ipv4 meta l4proto { tcp, udp } th dport 53 counter dnat ip to '+local4+':'+port+'\n';
 if(local6)text+='add rule inet blaze_sites dns iifname '+interfaces+' '+match+' meta nfproto ipv6 meta l4proto { tcp, udp } th dport 53 counter dnat ip6 to ['+local6+']:'+port+'\n';
 else text+='add rule inet blaze_sites dns iifname '+interfaces+' '+match+' meta nfproto ipv6 meta l4proto { tcp, udp } th dport 53 drop\n';
}
for(let i=0;i<length(p.devices);i++)add(p.devices[i],1054+i,'ether saddr '+p.devices[i].mac);
if(p.mode!='off')add(p,1053,'');
writefile('/tmp/blaze-sites.nft',text);run('nft -c -f /tmp/blaze-sites.nft');run('nft -f /tmp/blaze-sites.nft');unlink('/tmp/blaze-sites.nft');
writefile('/tmp/blaze-sites-coverage.json',sprintf('%J',{interfaces:devs,ap_dns:true,encrypted_dns:false,hardware_switched_paths:false,time:time()}));
