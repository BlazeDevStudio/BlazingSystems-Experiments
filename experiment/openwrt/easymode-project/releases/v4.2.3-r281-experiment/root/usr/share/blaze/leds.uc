import {readfile,writefile} from 'fs';
import {quote,exec,readjson} from '/usr/share/blaze/common.uc';
function ledSettings(u){return {mode:u.get('blaze','leds','mode')||'native',metric:u.get('blaze','leds','metric')||'rsrp',threshold1:int(u.get('blaze','leds','threshold1')||25),threshold2:int(u.get('blaze','leds','threshold2')||50),threshold3:int(u.get('blaze','leds','threshold3')||75),duration:int(u.get('blaze','leds','duration')||60),expires:int(u.get('blaze','leds','expires')||0)};}
function ledProfile(p){
 if(!(p.mode in ['native','signal','dance']))die('Invalid LED mode.');
 if(!(p.metric in ['csq','rssi','rsrp','rsrq','sinr']))die('Invalid LED metric.');
 for(let k in ['threshold1','threshold2','threshold3','duration'])if(type(p[k])!='int'||p[k]<0)die('LED thresholds and duration must be whole numbers.');
 if(p.threshold1>=p.threshold2||p.threshold2>=p.threshold3||p.threshold3>100)die('Choose increasing thresholds between 0 and 100 percent.');
 if(p.duration>86400)die('LED timer maximum is 24 hours; zero means permanent.');
 return {mode:p.mode,metric:p.metric,threshold1:p.threshold1,threshold2:p.threshold2,threshold3:p.threshold3,duration:p.duration,expires:p.mode=='dance'&&p.duration?time()+p.duration:0};
}
function ledQuality(r,metric){
 let ranges={csq:[0,31],rssi:[-113,-51],rsrp:[-140,-80],rsrq:[-20,-3],sinr:[-20,30]},v=r[metric],b=ranges[metric];
 if(!r.available||!b||v==null||(metric=='csq'&&v==99)||time()-int(r.time||0)>120)return null;
 return max(0,min(100,(v-b[0])*100/(b[1]-b[0])));
}
function cp(cmd){
 if(length(cmd)>430)die('CP LED command too long.');
 let x=exec('/usr/bin/sms_tool -d /dev/ttyACM0 at '+quote('AT%EXE="'+cmd+'"'));
 if(x.rc)die('Modem LED control did not answer.');
 return replace(x.out,/\r/g,'');
}
function helper(){
 let source='/usr/share/blaze/cp-led.sh',expected=split(trim(exec('md5sum '+source).out),' ')[0],have=cp('md5sum /tmp/blaze-led-script.sh');
 if(index(have,expected)>=0)return;
 let data=readfile(source);if(!data)die('CP LED helper missing.');
 cp(': >/tmp/blaze-led-script.sh');
 for(let n=0;n<length(data);n+=32){let encoded='';for(let j=n;j<min(n+32,length(data));j++)encoded+=sprintf('\\\\x%02x',ord(substr(data,j,1)));cp("printf '"+encoded+"' >>/tmp/blaze-led-script.sh");}
 if(index(cp('md5sum /tmp/blaze-led-script.sh'),expected)<0)die('CP LED helper checksum mismatch. LEDs unchanged.');
}
function applyLED(p,force){
 let now=time(),mode=p.mode;if(mode=='dance'&&p.expires&&now>=p.expires)mode='native';
 let old=readjson('/tmp/blaze-led.json',{}),r=readjson('/tmp/blaze-radio.json',{}),quality=ledQuality(r,p.metric),level=0;
 if(quality!=null)for(let k in ['threshold1','threshold2','threshold3'])if(quality>=p[k])level++;
 let key=mode+':'+(mode=='signal'?level:'')+':'+p.metric+':'+p.expires;
 if(!force&&((mode=='native'&&!old.key&&!old.error)||(old.key==key&&now-int(old.time||0)<300)))return old;
 helper();now=time();if(force&&mode=='dance'&&p.duration)p.expires=now+p.duration;key=mode+':'+(mode=='signal'?level:'')+':'+p.metric+':'+p.expires;let duration=mode=='dance'&&p.expires?max(1,p.expires-now):0,token=trim(readfile('/proc/sys/kernel/random/uuid'));
 let response=cp('sh /tmp/blaze-led-script.sh '+mode+' '+level+' '+duration+' '+token);
 if(index(response,'\nBLAZELED:'+mode+'\n')<0)die('LED change was not confirmed.');
 let result={key,time:now,mode,metric:p.metric,quality,level:mode=='signal'?level:null,expires:p.expires,error:''};writefile('/tmp/blaze-led.json',sprintf('%J',result));return result;
}
export {ledSettings,ledProfile,ledQuality,applyLED};
