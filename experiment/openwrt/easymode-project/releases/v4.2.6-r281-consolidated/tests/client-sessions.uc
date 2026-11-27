import {advance} from '../root/usr/share/blaze/client-sessions.uc';
function check(x,m){if(!x)die(m);}
let mac='02:11:22:33:44:55',seen={mac,online:true,medium:'Wi-Fi',ip:'192.0.2.5',name:'Test device'};
let s=advance({},[seen],1000,10,'boot-a');
check(s.devices[mac].online&&s.devices[mac].session_seconds==0,'first observation must not invent earlier history');
s=advance(s,[seen],1060,70,'boot-a');
check(s.devices[mac].total_seconds==60&&s.devices[mac].session_seconds==60,'one minute credited');
s=advance(s,[seen],900,130,'boot-a');
check(s.devices[mac].total_seconds==120,'clock adjustment must not alter monotonic duration');
s=advance(s,[],960,190,'boot-a');
check(!s.devices[mac].online&&s.devices[mac].history[0].seconds==120,'Wi-Fi departure closes session');
s=advance(s,[seen],1020,250,'boot-a');
check(s.devices[mac].session_seconds==0&&s.devices[mac].total_seconds==120,'reconnect starts a new session');
s=advance(s,[seen],1080,310,'boot-a');
s=advance(s,[seen],8000,10,'boot-b');
check(s.devices[mac].total_seconds==180&&s.devices[mac].session_seconds==0,'reboot must not count downtime');
s=advance(s,[seen],9000,1010,'boot-b');
check(s.devices[mac].total_seconds==180&&s.devices[mac].session_seconds==0,'monitoring gap must not count unobserved time');
let w={...seen,medium:'LAN',online:true};s=advance({},[w],1000,10,'boot-c');
s=advance(s,[],1060,70,'boot-c');check(s.devices[mac].online,'wired grace window');
s=advance(s,[],1241,251,'boot-c');check(!s.devices[mac].online,'stale wired observation must expire');
for(let i=0;i<20;i++){s=advance(s,[seen],2000+i*120,1000+i*120,'boot-c');s=advance(s,[],2060+i*120,1060+i*120,'boot-c');}
check(length(s.devices[mac].history)<=8,'bounded history');
let many=[];for(let i=0;i<140;i++)push(many,{mac:sprintf('02:11:22:33:44:%02x',i),online:false});
s=advance({},many,5000,100,'boot-d');check(length(keys(s.devices))<=128,'bounded device count');
print('PASS: session transitions, clock changes, reboot, sampling gaps, wired expiry and bounded retention\n');
