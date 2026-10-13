// Execute only with an isolated UCI directory supplied by the test launcher.
import {cursor} from 'uci';
import {ssidProfile,applySSID,bindings} from '/tmp/ssid-test/ssid.uc';
let u=cursor('/tmp/ssid-test/config'),n=0;
function check(v,label){if(!v)die(label);n++;}
function rejects(p,label){let rejected=false;try{ssidProfile(u,p);}catch(e){rejected=true;}check(rejected,label);}
let p={section:'',ssid:'Test AP',device:'radio0',network:'lan',encryption:'psk2',password:'TestOnly123',enabled:false};
let id=applySSID(u,p);check(u.get('wireless',id,'network')=='lan','LAN binding committed');
check(u.get('wireless',id,'disabled')=='1','disabled state committed');
p.section=id;p.password='';check(ssidProfile(u,p).key=='TestOnly123','blank retains saved key');
p.network='blaze_repeat';applySSID(u,p);check(u.get('wireless',id,'network')=='blaze_repeat','custom SSID repeater binding');
p.network='piso';rejects(p,'Piso unavailable until configured');
u.set('blaze','main','mode','piso');u.set('network','piso','interface');u.set('network','piso','proto','none');
applySSID(u,p);check(u.get('wireless',id,'network')=='piso'&&u.get('wireless',id,'isolate')=='1','Piso VLAN binding and isolation');
rejects({...p,section:'sta'},'cannot edit station as AP');
rejects({...p,section:'../../etc/passwd'},'invalid section rejected');
rejects({...p,network:'wan'},'WAN binding rejected');
rejects({...p,section:'primary',network:'piso'},'primary binding protected');
rejects({...p,ssid:''},'empty name rejected');
rejects({...p,password:'short'},'short password rejected');
rejects({...p,device:'bad'},'invalid radio rejected');
print('PASS: '+n+' isolated SSID validation and UCI transformation checks\n');
