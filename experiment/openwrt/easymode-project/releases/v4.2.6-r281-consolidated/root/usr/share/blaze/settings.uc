import {saveRepeater,configureRepeater} from '/usr/share/blaze/repeater.uc';
import {applyUplink} from '/usr/share/blaze/uplink.uc';
import {config,checked,readjson} from '/usr/share/blaze/common.uc';
let p=readjson('/tmp/blaze-settings-request.json',{}),u=config();
if(p.kind=='wifi'){
 let count=0;
 u.foreach('wireless','wifi-iface',s=>{if(s.mode=='ap'&&s.network=='lan'){
  let id=s['.name'];u.set('wireless',id,'ssid',p.ssid);if(p.password){u.set('wireless',id,'key',p.password);u.set('wireless',id,'encryption','psk2');}u.set('wireless',id,'disabled',p.enabled?'0':'1');count++;
 }});
 if(count!=2)die('Expected two home Wi-Fi interfaces. No settings committed.');
 if(u.get('wireless','blaze_repeat')&&(u.get('blaze','repeater','security')||'inherit')=='inherit')configureRepeater(u);
 u.commit('wireless');
}else if(p.kind=='piso_wifi'){
 u.set('blaze','main','piso_ssid_2g',p.ssid2g);u.set('blaze','main','piso_ssid_5g',p.ssid5g);u.set('blaze','main','piso_2g_enabled',p.enabled2g?'1':'0');u.set('blaze','main','piso_5g_enabled',p.enabled5g?'1':'0');u.commit('blaze');
 let rows=[['piso2g',p.ssid2g,p.enabled2g],['piso5g',p.ssid5g,p.enabled5g]];for(let row in rows){let id=row[0],name=row[1],enabled=row[2];if(u.get('wireless',id)){u.set('wireless',id,'ssid',name);u.set('wireless',id,'disabled',enabled?'0':'1');}}
 u.commit('wireless');
}else if(p.kind=='repeater_ap'){
 saveRepeater(u,p);if(u.get('wireless','blaze_repeat'))configureRepeater(u);u.commit('blaze');u.commit('wireless');
}else if(p.kind=='wifi_sta'){
 applyUplink(u,p);
}else if(p.kind=='apn'){
 checked('mkdir -p /etc/blaze; cp /etc/config/network /etc/blaze/network-apn-before');
 u.set('network','wwan','apn',p.apn);u.commit('network');
}else die('Unknown settings operation');
