import {readfile,writefile} from 'fs';
import {config,checked,readjson} from '/usr/share/blaze/common.uc';
let p=readjson('/tmp/blaze-mode-request.json',null);if(!p)die('Missing mode request');
if(!(p.port1 in ['wan','lan'])||!(p.mode in ['standard','piso']))die('Invalid mode');
if(p.mode=='piso'&&(int(p.vlan)<2||int(p.vlan)>4094))die('Invalid VLAN');
checked('mkdir -p /etc/blaze; for f in network firewall wireless dhcp blaze; do cp /etc/config/$f /etc/blaze/$f-before || exit; done');
writefile('/etc/blaze/mode-pending','1');
let u=config(),bridge=null;u.foreach('network','device',s=>{if(s.name=='br-lan')bridge=s['.name'];});if(!bridge)die('LAN bridge not found');
u.set('network',bridge,'ports',p.port1=='lan'?['wan','lan1','lan2','lan3']:['lan1','lan2','lan3']);
u.set('network',bridge,'vlan_filtering',p.mode=='piso'?'1':'0');
u.set('network','wan','auto',p.port1=='wan'?'1':'0');
for(let s in ['blaze_native','blaze_piso','piso'])u.delete('network',s);
for(let s in ['piso2g','piso5g'])u.delete('wireless',s);
if(p.mode=='piso'){
 u.set('network','blaze_native','bridge-vlan');u.set('network','blaze_native','device','br-lan');u.set('network','blaze_native','vlan','1');
 u.set('network','blaze_native','ports',p.port1=='lan'?['wan:u*','lan2:u*','lan3:u*']:['lan2:u*','lan3:u*']);
 u.set('network','blaze_piso','bridge-vlan');u.set('network','blaze_piso','device','br-lan');u.set('network','blaze_piso','vlan',''+p.vlan);u.set('network','blaze_piso','ports',['lan3:t','lan2:t','lan1:u*']);
 u.set('network','lan','device','br-lan.1');u.set('network','piso','interface');u.set('network','piso','proto','none');u.set('network','piso','device','br-lan.'+p.vlan);
 let n2=u.get('blaze','main','piso_ssid_2g')||'BlazeSystems-PisoWiFi',n5=u.get('blaze','main','piso_ssid_5g')||'BlazeSystems-PisoWiFi-5G',e2=u.get('blaze','main','piso_2g_enabled')!='0',e5=u.get('blaze','main','piso_5g_enabled')!='0';
 for(let b in ['2g','5g']){let s='piso'+b,is5=b=='5g';u.set('wireless',s,'wifi-iface');u.set('wireless',s,'device',is5?'radio1':'radio0');u.set('wireless',s,'mode','ap');u.set('wireless',s,'ssid',is5?n5:n2);u.set('wireless',s,'network','piso');u.set('wireless',s,'encryption','none');u.set('wireless',s,'isolate','1');u.set('wireless',s,'disabled',(is5?e5:e2)?'0':'1');}
}else u.set('network','lan','device','br-lan');
// Split each upstream into its own firewall zone. The SIM remains isolated from management.
u.foreach('firewall','zone',s=>{if(s.name=='wan')u.set('firewall',s['.name'],'network',['wwan']);});
u.set('firewall','blaze_wired','zone');for(let k,v in {name:'wired',input:'REJECT',output:'ACCEPT',forward:'REJECT',masq:'1',mtu_fix:'1'})u.set('firewall','blaze_wired',k,v);u.set('firewall','blaze_wired','network',['wan']);
u.set('firewall','blaze_wired_forward','forwarding');u.set('firewall','blaze_wired_forward','src','lan');u.set('firewall','blaze_wired_forward','dest','wired');
u.set('firewall','blaze_wired_dhcp','rule');for(let k,v in {name:'Blaze wired DHCP',src:'wired',proto:'udp',dest_port:'68',family:'ipv4',target:'ACCEPT'})u.set('firewall','blaze_wired_dhcp',k,v);
u.set('firewall','blaze_wired_admin','rule');for(let k,v in {name:'Blaze upstream administration',src:'wired',proto:'tcp',dest_port:'80 443 22',family:'ipv4',target:'ACCEPT'})u.set('firewall','blaze_wired_admin',k,v);u.set('firewall','blaze_wired_admin','src_ip',['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16']);
if(u.get('network','wifiwan')&&u.get('blaze','main','wifi_uplink_mode')!='relay'){u.set('firewall','blaze_wifiwan','zone');for(let k,v in {name:'wifiwan',input:'REJECT',output:'ACCEPT',forward:'REJECT',masq:'1',mtu_fix:'1'})u.set('firewall','blaze_wifiwan',k,v);u.set('firewall','blaze_wifiwan','network',['wifiwan']);u.set('firewall','blaze_wifiwan_forward','forwarding');u.set('firewall','blaze_wifiwan_forward','src','lan');u.set('firewall','blaze_wifiwan_forward','dest','wifiwan');}
if(u.get('network','wifiwan')){u.set('firewall','blaze_wifiwan_dhcp','rule');for(let k,v in {name:'Wi-Fi uplink DHCP renewal',src:'wifiwan',proto:'udp',dest_port:'68',family:'ipv4',target:'ACCEPT'})u.set('firewall','blaze_wifiwan_dhcp',k,v);}
u.set('firewall','blaze_piso','zone');for(let k,v in {name:'piso',input:'REJECT',output:'REJECT',forward:'REJECT'})u.set('firewall','blaze_piso',k,v);u.set('firewall','blaze_piso','network',['piso']);
u.set('dhcp','piso','dhcp');u.set('dhcp','piso','interface','piso');u.set('dhcp','piso','ignore','1');u.set('dhcp','piso','ra','disabled');u.set('dhcp','piso','dhcpv6','disabled');
for(let n in ['network','firewall','wireless','dhcp'])u.commit(n);
let result=system('fw4 check >/tmp/blaze-firewall-check 2>&1');
if(result){checked('for f in network firewall wireless dhcp blaze; do cp /etc/blaze/$f-before /etc/config/$f || exit; done');die('Firewall validation failed; settings restored');}
for(let k in ['port1','mode','vlan'])u.set('blaze','main',k,''+p[k]);u.commit('blaze');
checked('/etc/init.d/network reload; /etc/init.d/firewall reload; /etc/init.d/dnsmasq reload; wifi reload');
