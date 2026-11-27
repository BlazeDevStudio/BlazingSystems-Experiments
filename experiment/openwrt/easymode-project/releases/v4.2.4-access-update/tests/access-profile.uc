import {profile,rules} from '/usr/share/blaze/access.uc';
function check(x,s){if(!x)die(s);}
function rejects(p){try{profile(p);}catch(e){return;}die('Invalid policy accepted');}
rejects({mode:'allow',scope:'all',macs:[]});
rejects({mode:'deny',scope:'all',macs:['aa:bb:cc:dd:ee:ff; reboot']});
rejects({mode:'deny',scope:'wan',macs:[]});
rejects({mode:'deny',scope:'all',macs:['ff:ff:ff:ff:ff:ff']});
let p=profile({mode:'deny',scope:'all',macs:['02:AA:BB:CC:DD:EE','02:aa:bb:cc:dd:ee']});
check(length(p.macs)==1&&p.macs[0]=='02:aa:bb:cc:dd:ee','canonical deduplication');
check(index(rules(p),'ether saddr @client_macs counter drop')>=0,'deny rule');
check(index(rules(profile({mode:'allow',scope:'all',macs:p.macs})),'ether saddr != @client_macs counter drop')>=0,'allow rule');
check(index(rules(profile({mode:'off',scope:'all',macs:[]})),'counter drop')<0,'off must not filter');
print('PASS: access validation and rule generation\n');


