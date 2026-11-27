import {cursor} from 'uci';
import {repeaterSettings,repeaterProfile,saveRepeater,configureRepeater} from '/usr/share/blaze/repeater.uc';
let u=cursor('/tmp/blaze-repeater-fixture');
function check(x,m){if(!x)die(m);}
let before=sprintf('%J',u.get_all('wireless','blaze_sta'));
saveRepeater(u,{ssid:'Test repeat',security:'psk2',password:'fixture-password',radio:'radio0',enabled:true,portal_identity:'shared'});configureRepeater(u);
check(u.get('wireless','blaze_repeat','key')=='fixture-password','Custom key failed');
check(!repeaterSettings(u).key&&!repeaterSettings(u).password,'Secret exposed');
saveRepeater(u,{password:''});configureRepeater(u);check(u.get('wireless','blaze_repeat','key')=='fixture-password','Saved key lost');
saveRepeater(u,{security:'none'});configureRepeater(u);check(u.get('wireless','blaze_repeat','encryption')=='none'&&!u.get('wireless','blaze_repeat','key'),'Open key not removed');
saveRepeater(u,{security:'inherit',radio:'auto',enabled:false});configureRepeater(u);check(u.get('wireless','blaze_repeat','disabled')=='1','Disable failed');
check(u.get('wireless','blaze_repeat','key')!='','Inheritance failed');
for(let p in [{ssid:''},{security:'bad'},{security:'psk2',password:'short'},{radio:'bad'},{enabled:'0'},{portal_identity:'bad'}]){let rejected=false;try{repeaterProfile(u,p);}catch(e){rejected=true;}check(rejected,'Invalid input accepted');}
check(before==sprintf('%J',u.get_all('wireless','blaze_sta')),'Upstream changed');
print('PASS: custom, keep key, open, inherit, disabled, radio, identity, invalid input, secret redaction and upstream unchanged\n');
