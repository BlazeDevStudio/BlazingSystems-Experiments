import {hasControl} from '/usr/share/blaze/common.uc';
function bindings(u){return [
 {id:'lan',label:'LAN / home network',available:!!u.get('network','lan')},
 {id:'blaze_repeat',label:'Wi-Fi repeater / upstream DHCP',available:!!u.get('network','blaze_repeat')&&u.get('blaze','main','wifi_uplink_mode')=='relay'&&u.get('blaze','main','wifi_relay_scope')=='ssid'},
 {id:'piso',label:'PisoWiFi VLAN '+(u.get('blaze','main','vlan')||''),available:u.get('blaze','main','mode')=='piso'&&!!u.get('network','piso')}
];}
function ssidProfile(u,p){
 let id=p.section || '',old=id?u.get_all('wireless',id):null;
 if(id && (!match(id,/^[A-Za-z0-9_]{1,64}$/)||!old||old['.type']!='wifi-iface'||old.mode!='ap'))die('Select an existing access point.');
 if(type(p.ssid)!='string'||!length(p.ssid)||length(p.ssid)>32||hasControl(p.ssid,true))die('Wi-Fi name must be 1-32 bytes without control characters.');
 if(!(p.device in ['radio0','radio1'])||!u.get('wireless',p.device))die('Select an available radio.');
 if(type(p.enabled)!='bool')die('Enabled must be a boolean.');
 let binding=null;for(let b in bindings(u))if(b.id==p.network)binding=b;
 if(!binding?.available)die('Configure this network first under Wi-Fi uplink or Internet & ports.');
 // Primary APs are owned by established home/repeater/Piso workflows.
 if(old && !match(id,/^blaze_ssid_/) && (old.network!=p.network||old.device!=p.device))die('Primary AP binding and radio are managed by their existing setup. Add an SSID for another binding.');
 if(!(p.encryption in ['psk2','sae-mixed','none']))die('Choose WPA2, WPA2/WPA3 or open security.');
 if(id=='blaze_repeat'&&p.encryption=='sae-mixed')die('Use WPA2 or open security for the primary repeater AP.');
 let key=p.password || (old?.encryption==p.encryption?old.key:'') || '';
 if(p.encryption!='none'&&(type(key)!='string'||length(key)<8||length(key)>63||hasControl(key,true)))die('Set an 8-63 character password, or leave blank to retain the same security password.');
 let count=0;u.foreach('wireless','wifi-iface',s=>{if(s.device==p.device&&s['.name']!=id)count++;});
 if(count>=8)die('Radio interface limit reached. Disable/remove unused interfaces in Advanced settings.');
 return {section:id,ssid:p.ssid,device:p.device,network:p.network,encryption:p.encryption,key,enabled:p.enabled};
}
function applySSID(u,p){let v=ssidProfile(u,p),id=v.section;
 if(!id){for(let i=1;i<=64;i++)if(!u.get('wireless','blaze_ssid_'+i)){id='blaze_ssid_'+i;break;}if(!id)die('SSID capacity reached.');u.set('wireless',id,'wifi-iface');}
 for(let k in ['ssid','device','network','encryption'])u.set('wireless',id,k,v[k]);
 u.set('wireless',id,'mode','ap');u.set('wireless',id,'disabled',v.enabled?'0':'1');
 if(v.encryption=='none')u.delete('wireless',id,'key');else u.set('wireless',id,'key',v.key);
 if(v.network=='piso')u.set('wireless',id,'isolate','1');
 if(id=='blaze_repeat'){
  u.set('blaze','repeater','repeater');for(let k,vv in {ssid:v.ssid,radio:v.device,security:v.encryption,enabled:v.enabled?'1':'0'})u.set('blaze','repeater',k,vv);
  // Repeater's existing profile accepts WPA2/open; validate this in the caller.
  if(v.encryption=='none')u.delete('blaze','repeater','key');else u.set('blaze','repeater','key',v.key);
  u.set('blaze','main','wifi_repeat_ssid',v.ssid);
 }
 if(id in ['piso2g','piso5g']){let band=id=='piso2g'?'2g':'5g';u.set('blaze','main','piso_ssid_'+band,v.ssid);u.set('blaze','main','piso_'+band+'_enabled',v.enabled?'1':'0');}
 if(!u.commit('wireless')||!u.commit('blaze'))die('SSID configuration could not be saved.');return id;
}
export {bindings,ssidProfile,applySSID};
