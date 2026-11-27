// UCI-only transformation. Jobs own snapshots, validation and service reloads.
function section(u,c,id,type,values){u.set(c,id,type);for(let k,v in values)u.set(c,id,k,v);}
function clearRelay(u){
 let raw=u.get('blaze','main','relay_saved_dhcp');
 if(raw){let saved=json(raw);for(let k in ['ignore','dhcpv4','dhcpv6','ra','ndp']){if(saved[k]!=null)u.set('dhcp','lan',k,saved[k]);else u.delete('dhcp','lan',k);}u.delete('blaze','main','relay_saved_dhcp');}
 for(let c,ids in {network:['blaze_relay','blaze_backup','blaze_backup_dev','blaze_repeat','blaze_repeat_dev'],dhcp:['blaze_backup','blaze_repeat'],wireless:['blaze_backup','blaze_repeat'],firewall:['blaze_repeat','blaze_repeat_admin','blaze_relay_back','blaze_wifiwan_admin','blaze_backup','blaze_backup_sim','blaze_backup_wired']})for(let id in ids)u.delete(c,id);
}
function applyUplink(u,p){
 clearRelay(u);
 section(u,'firewall','blaze_relay_compat','include',{type:'script',path:'/usr/libexec/blaze-relay-firewall',fw4_compatible:'1'});
 let prevRadio=u.get('blaze','main','wifi_sta_prev_radio')||'',prevChannel=u.get('blaze','main','wifi_sta_prev_channel')||'';
 if(p.disconnect){
  u.delete('wireless','blaze_sta');u.delete('network','wifiwan');
  for(let id in ['blaze_wifiwan','blaze_wifiwan_forward','blaze_wifiwan_dhcp'])u.delete('firewall',id);
  if(prevRadio&&prevChannel)u.set('wireless',prevRadio,'channel',prevChannel);
  for(let k in ['wifi_sta_prev_radio','wifi_sta_prev_channel','wifi_sta_channel','wifi_uplink_mode','wifi_captive','wifi_backup','wifi_relay_scope','wifi_repeat_ssid'])u.delete('blaze','main',k);
 }else{
  let relay=p.mode=='relay',dedicated=relay&&p.scope=='ssid';
  if(prevRadio&&prevRadio!=p.radio&&prevChannel)u.set('wireless',prevRadio,'channel',prevChannel);
  if(!prevRadio||prevRadio!=p.radio){u.set('blaze','main','wifi_sta_prev_radio',p.radio);u.set('blaze','main','wifi_sta_prev_channel',u.get('wireless',p.radio,'channel')||'auto');}
  section(u,'network','wifiwan','interface',{proto:'dhcp',metric:'25',peerdns:dedicated?'0':'1'});
  section(u,'wireless','blaze_sta','wifi-iface',{device:p.radio,mode:'sta',network:'wifiwan',ssid:p.ssid,encryption:p.encryption,disabled:'0'});
  let channel=int(p.channel||0)>0?''+int(p.channel):'auto';u.set('wireless',p.radio,'channel',channel);u.set('blaze','main','wifi_sta_channel',channel);
  if(p.bssid)u.set('wireless','blaze_sta','bssid',p.bssid);else u.delete('wireless','blaze_sta','bssid');
  if(p.encryption!='none')u.set('wireless','blaze_sta','key',p.password);else u.delete('wireless','blaze_sta','key');
  section(u,'firewall','blaze_wifiwan','zone',{name:'wifiwan',input:'REJECT',output:'ACCEPT',forward:'REJECT',masq:relay?'0':'1',mtu_fix:'1',network:['wifiwan']});
  section(u,'firewall','blaze_wifiwan_forward','forwarding',{src:dedicated?'blaze_repeat':'lan',dest:'wifiwan'});
  section(u,'firewall','blaze_wifiwan_dhcp','rule',{name:'Wi-Fi uplink DHCP renewal',src:'wifiwan',proto:'udp',dest_port:'68',family:'ipv4',target:'ACCEPT'});
  u.set('blaze','main','wifi_uplink_mode',relay?'relay':'routed');u.set('blaze','main','wifi_captive',p.captive?'1':'0');u.set('blaze','main','wifi_backup',p.backup&&!dedicated?'1':'0');u.set('blaze','main','wifi_relay_scope',dedicated?'ssid':'lan');
  if(relay){
   if(!dedicated){
   let saved={};for(let k in ['ignore','dhcpv4','dhcpv6','ra','ndp'])saved[k]=u.get('dhcp','lan',k);
   u.set('blaze','main','relay_saved_dhcp',sprintf('%J',saved));
   u.set('dhcp','lan','ignore','1');for(let k in ['dhcpv4','dhcpv6','ra','ndp'])u.set('dhcp','lan',k,'disabled');
   }
   section(u,'network','blaze_relay','interface',{proto:'relay',network:[dedicated?'blaze_repeat':'lan','wifiwan'],forward_bcast:'1',forward_dhcp:'1'});
   section(u,'firewall','blaze_relay_back','forwarding',{src:'wifiwan',dest:dedicated?'blaze_repeat':'lan'});
   section(u,'firewall','blaze_wifiwan_admin','rule',{name:'Repeater authenticated administration',src:'wifiwan',proto:'tcp',dest_port:'80 443',family:'ipv4',target:'ACCEPT',src_ip:['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16']});
   if(dedicated){
    let ap=null;u.foreach('wireless','wifi-iface',s=>{if(!ap&&s.mode=='ap'&&s.network=='lan'&&s.key)ap=s;});
    if(!ap)die('A protected home Wi-Fi is required to secure the repeater SSID.');
    let name=p.repeat_ssid||substr(ap.ssid,0,23)+'-Repeater';
    section(u,'network','blaze_repeat_dev','device',{name:'br-blaze-repeat',type:'bridge'});
    section(u,'network','blaze_repeat','interface',{proto:'static',device:'br-blaze-repeat',ipaddr:'192.168.253.1',netmask:'255.255.255.0'});
    section(u,'dhcp','blaze_repeat','dhcp',{interface:'blaze_repeat',ignore:'1',dhcpv4:'disabled',dhcpv6:'disabled',ra:'disabled'});
    section(u,'wireless','blaze_repeat','wifi-iface',{device:p.radio=='radio0'?'radio1':'radio0',mode:'ap',network:'blaze_repeat',ssid:name,encryption:ap.encryption,key:ap.key,disabled:'0'});
    section(u,'firewall','blaze_repeat','zone',{name:'blaze_repeat',network:['blaze_repeat'],input:'REJECT',output:'ACCEPT',forward:'REJECT'});
    section(u,'firewall','blaze_repeat_admin','rule',{name:'Repeater local administration',src:'blaze_repeat',proto:'tcp',dest_port:'80 443',family:'ipv4',target:'ACCEPT'});
    u.set('blaze','main','wifi_repeat_ssid',name);
   }
   if(p.backup&&!dedicated){
    let ap=null;u.foreach('wireless','wifi-iface',s=>{if(!ap&&s.mode=='ap'&&s.network=='lan'&&s.key)ap=s;});
    if(!ap)die('A protected home Wi-Fi is required for the backup access point.');
    section(u,'network','blaze_backup_dev','device',{name:'br-blaze-backup',type:'bridge'});
    section(u,'network','blaze_backup','interface',{proto:'static',device:'br-blaze-backup',ipaddr:'192.168.254.1',netmask:'255.255.255.0'});
    section(u,'dhcp','blaze_backup','dhcp',{interface:'blaze_backup',start:'100',limit:'100',leasetime:'1h',ignore:'0',dhcpv4:'server',dhcpv6:'disabled',ra:'disabled'});
    section(u,'wireless','blaze_backup','wifi-iface',{device:p.radio=='radio0'?'radio1':'radio0',mode:'ap',network:'blaze_backup',ssid:substr(ap.ssid,0,25)+'-Backup',encryption:ap.encryption,key:ap.key,disabled:'0'});
    section(u,'firewall','blaze_backup','zone',{name:'blaze_backup',network:['blaze_backup'],input:'ACCEPT',output:'ACCEPT',forward:'REJECT'});
    section(u,'firewall','blaze_backup_sim','forwarding',{src:'blaze_backup',dest:'wan'});
    section(u,'firewall','blaze_backup_wired','forwarding',{src:'blaze_backup',dest:'wired'});
   }
  }
 }
 // All validation above occurs before any commit.
 for(let c in ['network','wireless','firewall','dhcp','blaze'])if(!u.commit(c))die('Could not commit '+c);
}
export {applyUplink};
