import {hasControl} from '/usr/share/blaze/common.uc';
function homeAP(u){let ap=null;u.foreach('wireless','wifi-iface',s=>{if(!ap&&s.mode=='ap'&&s.network=='lan')ap=s;});return ap;}
function repeaterSettings(u){return {portal_identity:u.get('blaze','repeater','portal_identity')||'separate',ssid:u.get('blaze','repeater','ssid')||u.get('blaze','main','wifi_repeat_ssid')||'BlazeSystems-Repeater',security:u.get('blaze','repeater','security')||'inherit',radio:u.get('blaze','repeater','radio')||'auto',enabled:u.get('blaze','repeater','enabled')!='0',has_password:!!u.get('blaze','repeater','key')};}
function repeaterProfile(u,p){
 let saved=repeaterSettings(u),ssid=p.ssid??saved.ssid,security=p.security??saved.security,radio=p.radio??saved.radio,enabled=p.enabled??saved.enabled,portal_identity=p.portal_identity??saved.portal_identity;
 if(type(enabled)!='bool')die('Enabled must be a boolean.');
 if(!(portal_identity in ['separate','shared']))die('Invalid portal compatibility mode.');
 if(type(ssid)!='string'||!length(ssid)||length(ssid)>32||hasControl(ssid,true))die('Repeater name must be 1–32 bytes without control characters.');
 if(!(security in ['inherit','psk2','none']))die('Choose home password, WPA2 or open security.');
 if(!(radio in ['auto','radio0','radio1']))die('Invalid repeater AP radio.');
 let ap=homeAP(u),key='',encryption='none';
 if(security=='inherit'){if(!ap?.key)die('Home Wi-Fi has no password to inherit. Choose open or a custom password.');key=ap.key;encryption=ap.encryption;}
 else if(security=='psk2'){key=p.password||u.get('blaze','repeater','key')||'';if(type(key)!='string'||length(key)<8||length(key)>63||hasControl(key,true))die('Repeater password must be 8–63 bytes. Leave it blank only to keep an existing custom password.');encryption='psk2';}
 return {ssid,security,radio,portal_identity,enabled:enabled!==false,key,encryption};
}
function saveRepeater(u,p){let v=repeaterProfile(u,p);u.set('blaze','repeater','repeater');for(let k in ['ssid','security','radio','portal_identity'])u.set('blaze','repeater',k,v[k]);u.set('blaze','repeater','enabled',v.enabled?'1':'0');if(v.security=='psk2')u.set('blaze','repeater','key',v.key);else u.delete('blaze','repeater','key');return v;}
function configureRepeater(u,p){p=p||{};
 let v=repeaterProfile(u,p),sta=u.get('wireless','blaze_sta','device')||'radio0';
 u.set('wireless','blaze_repeat','wifi-iface');u.set('wireless','blaze_repeat','device',v.radio=='auto'?(sta=='radio0'?'radio1':'radio0'):v.radio);u.set('wireless','blaze_repeat','mode','ap');u.set('wireless','blaze_repeat','network','blaze_repeat');u.set('wireless','blaze_repeat','ssid',v.ssid);u.set('wireless','blaze_repeat','encryption',v.encryption);u.set('wireless','blaze_repeat','disabled',v.enabled?'0':'1');if(v.encryption=='none')u.delete('wireless','blaze_repeat','key');else u.set('wireless','blaze_repeat','key',v.key);u.set('blaze','main','wifi_repeat_ssid',v.ssid);
 return v;
}
export {repeaterSettings,repeaterProfile,saveRepeater,configureRepeater};
