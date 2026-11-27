import {ledProfile,ledQuality} from '/usr/share/blaze/leds.uc';
function check(v,m){if(!v)die(m);}
let r={available:true,time:time(),csq:31,rsrp:-110,rssi:-82,rsrq:-11.5,sinr:5};
check(ledQuality(r,'csq')==100,'CSQ max');check(ledQuality(r,'rsrp')==50,'RSRP midpoint');check(ledQuality(r,'sinr')==50,'SINR midpoint');r.csq=99;check(ledQuality(r,'csq')==null,'Unknown CSQ');r.time=1;check(ledQuality(r,'rsrp')==null,'Stale measurement');
let p={mode:'dance',metric:'rsrp',threshold1:25,threshold2:50,threshold3:75,duration:12};check(ledProfile(p).expires>time(),'Timer');p.duration=0;check(ledProfile(p).expires==0,'Permanent');
for(let bad in [{...p,mode:'bad'},{...p,metric:'bad'},{...p,threshold2:20},{...p,threshold3:101},{...p,duration:86401},{...p,duration:-1}]){let rejected=false;try{ledProfile(bad);}catch(e){rejected=true;}check(rejected,'Invalid LED input accepted');}
print('PASS: signal scaling, stale/unknown input, permanent/timed duration and invalid settings\n');
