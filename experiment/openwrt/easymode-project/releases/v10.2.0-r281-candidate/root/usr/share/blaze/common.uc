import {popen,readfile,writefile} from 'fs';
import {cursor} from 'uci';
function quote(s) { return "'"+replace(''+s,"'","'\\''")+"'"; }
function exec(cmd) { let p=popen('('+cmd+') 2>&1','r'); if(!p)die('Cannot start operation'); let out=p.read('all'); let rc=p.close(); return {out,rc}; }
function checked(cmd) { let r=exec(cmd); if(r.rc)die(r.out || 'Operation failed'); return r.out; }
function readjson(path,fallback) { try{return json(readfile(path));}catch(e){return fallback;} }
function config() { return cursor(); }
function hasControl(s,all) { for(let i=0;i<length(s);i++){let n=ord(substr(s,i,1));if(n==0||n==26||(all&&(n<32||n==127)))return true;} return false; }
function smsLength(s){
 if(type(s)!='string'||!length(s))die('Enter a message.');
 let units=0;for(let i=0;i<length(s);i++){let c=substr(s,i,1),n=ord(c);if((n<32&&n!=10&&n!=13)||n>126||n==96)die('The installed SMS encoder supports basic Latin text and line breaks. Unicode sending requires an encoder upgrade.');units+=index('^{}\\[~]|',c)>=0?2:1;}
 if(units>160)die('One SMS supports 160 text units; ^ { } \\ [ ~ ] | count as two.');return units;
}
function normalize(number,operator) { let s=replace(trim(''+number),/[ ()-]/g,'');if(!match(s,/^\+?[0-9]{3,15}$/))die('Enter 3–15 digits, optionally starting with +.');return match(''+operator,/^515/)&&match(s,/^0[0-9]{10}$/)?'63'+substr(s,1):replace(s,/^\+/,''); }
function validbands(bands) {
 let a=split(trim(''+bands),/[, ]+/);if(!length(a))die('Choose at least one band.');let used={},sum=0;
 for(let b in a){if(!match(b,/^[0-9]+$/)||int(b)<1||int(b)>64)die('Invalid LTE band.');if(!used[b])sum+=2**(int(b)-1);used[b]=true;}
 return {mask:sprintf('%X',sum),bands:join(' ',keys(used))};
}
function parseRadio(s) {
 let csq=match(s,/\+CSQ:\s*([0-9]+)/),sig=match(s,/\+ZRSSI:\s*(-?[0-9.]+),(-?[0-9.]+),(-?[0-9.]+),(-?[0-9.]+)/),op=match(s,/\+COPS:.*"([0-9]+)"/),lock=match(s,/\+ZNLOCKBAND:\s*([A-Fa-f0-9]+),([A-Fa-f0-9]+)/),ca=match(s,/\+ZCAINFO:\s*([^\r\n]+)/);
 let carriers=[]; if(ca)for(let idx,row in split(ca[1],';')){let cols=split(trim(row),','),band=int(cols[idx==0?1:2]);if(length(cols)>=5&&band>0)push(carriers,{pci:int(cols[0]),band,earfcn:int(cols[3]),width:int(cols[4]),active:idx==0||int(cols[1])==2});}
 let mask=lock?hex(lock[1]):0,enabled=[];for(let b=1;b<=64;b++)if(mask&(1<<(b-1)))push(enabled,b);
 return {time:time(),available:!!sig,csq:csq?int(csq[1]):null,rsrp:sig?+sig[1]:null,rsrq:sig?+sig[2]:null,rssi:sig?+sig[3]:null,sinr:sig?+sig[4]:null,operator:op?.[1]||'',mode:length(filter(carriers,c=>c.active))>1?'LTE-A':'LTE',carriers,ca:length(filter(carriers,c=>c.active))>1,enabled,mask:lock?.[1]||'',gw_mask:lock?.[2]||'',source:'r281-at'};
}
function maybeNumber(v){let s=trim(''+(v||''));return match(s,/^-?[0-9]+([.][0-9]+)?$/)?+s:null;}
function bandFromText(v){let m=match(''+(v||''),/[BbNn]([0-9]+)/);return m?int(m[1]):0;}
function widthFromText(v){let m=match(''+(v||''),/@\s*([0-9.]+)\s*MHz/);return m?+m[1]:0;}
function genericRadio(){
 let r=exec("/usr/bin/timeout -k 1 7 /usr/bin/flock -x /var/lock/blaze-modem.lock sh /usr/share/3ginfo-lite/3ginfo.sh 2>/dev/null");if(r.rc)return {time:time(),available:false,source:'3ginfo',error:trim(r.out)};
 let j;try{j=json(r.out);}catch(e){return {time:time(),available:false,source:'3ginfo',error:'Could not parse generic modem status.'};}
 let carriers=[];for(let k in ['pband','s1band','s2band','s3band','s4band']){let b=bandFromText(j[k]);if(b>0&&!length(filter(carriers,c=>c.band==b)))push(carriers,{band:b,width:widthFromText(j[k]),active:true});}
 let mcc=(j.operator_mcc&&j.operator_mcc!='-')?j.operator_mcc:'',mnc=(j.operator_mnc&&j.operator_mnc!='-')?j.operator_mnc:'',reg=''+(j.registration||'');
 let rsrp=maybeNumber(j.rsrp),rsrq=maybeNumber(j.rsrq),rssi=maybeNumber(j.rssi),sinr=maybeNumber(j.sinr),csq=maybeNumber(j.csq);
 return {time:time(),available:rsrp!=null||csq!=null||reg in ['1','5','6','7'],csq,rsrp,rsrq,rssi,sinr,operator:mcc+mnc,operator_name:j.operator_name&&j.operator_name!='-'?j.operator_name:'',mode:j.mode&&j.mode!='-'?j.mode:'',modem:j.modem&&j.modem!='-'?j.modem:'',protocol:j.protocol&&j.protocol!='-'?j.protocol:'',simslot:j.simslot&&j.simslot!='-'?j.simslot:'',carriers,ca:length(carriers)>1,enabled:[],source:'3ginfo'};
}
function radio(){
 let pxa=exec("grep -q 'Vendor=1286 ProdID=4e28' /sys/kernel/debug/usb/devices 2>/dev/null && test -e /dev/ttyACM0");
 if(!pxa.rc){let r=exec("/usr/bin/timeout -k 1 7 /usr/bin/flock -x /var/lock/blaze-modem.lock /usr/bin/sms_tool -d /dev/ttyACM0 at 'AT+CSQ;+ZRSSI;+ZCELLINFO?;+ZCAINFO?;+COPS?;+ZNLOCKBAND?'");let out=parseRadio(r.out);if(out.available)return out;}
 return genericRadio();
}
export {smsLength,parseRadio,quote,exec,checked,readjson,config,normalize,validbands,radio,hasControl};
