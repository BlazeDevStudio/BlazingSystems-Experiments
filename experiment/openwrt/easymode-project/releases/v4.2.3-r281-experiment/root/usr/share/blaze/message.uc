import {readfile,writefile,rename,unlink,rmdir} from 'fs';
import {quote,exec,readjson} from '/usr/share/blaze/common.uc';
let id=trim(readfile('/tmp/blaze-message.lock/id')||''),p=readjson('/tmp/blaze-message.lock/request.json',{});
function detectPort(){let r=exec("/usr/share/3ginfo-lite/detect.sh 2>/dev/null | head -1"),port=trim(r.out||'');if(!match(port,/^\/dev\/[A-Za-z0-9._-]+$/)){if(readfile('/sys/class/tty/ttyACM0/dev'))port='/dev/ttyACM0';else die('No supported modem control port was detected.');}return port;}
function archiveSent(number,text,when,id){
 let path='/etc/blaze/sms-sent.json',h=readjson(path,{messages:[]}),old=type(h.messages)=='array'?h.messages:[],next=[];
 let start=length(old)>299?length(old)-299:0;for(let i=start;i<length(old);i++)push(next,old[i]);push(next,{id:id||'',number,text,time:when,status:'sent'});
 exec('mkdir -p /etc/blaze');writefile(path+'.new',sprintf('%J',{messages:next}));rename(path+'.new',path);exec('chmod 600 '+quote(path));
}
let result={id,pending:false,ok:false};
try {
 let port=detectPort(),command='flock -x /var/lock/blaze-modem.lock /usr/bin/sms_tool -d '+quote(port)+' ';
 if(p.kind=='inbox')command+='-s '+quote(p.storage)+' -f '+quote('%Y-%m-%d %H:%M:%S')+' -j recv';
 else if(p.kind=='send')command+='send '+quote(p.number)+' '+quote(p.text);
 else if(p.kind=='ussd')command+=(p.raw?'-R ':'')+(p.raw_output?'-r ':'')+'ussd '+quote(p.code);
 else die('Unknown message operation');
 let r=exec(command+' 2>/tmp/blaze-message.stderr'),error=trim(readfile('/tmp/blaze-message.stderr')||'');result.ok=r.rc==0;result.port=port;
 if(p.kind=='inbox'){
  if(r.rc)die(error||r.out||'Could not read modem storage.');let data=json(r.out);if(type(data.msg)!='array')die('Unexpected modem inbox format.');result.data=data;
 }else if(p.kind=='send'){
  result.ok=r.rc==0&&!!match(r.out,/sms sent suc{1,2}essfully/i);result.number=p.number;result.message=result.ok?'Modem accepted SMS to '+p.number+'. '+trim(r.out):'Send not confirmed. Do not retry automatically. '+trim(r.out+' '+error);
  if(result.ok){let sentAt=time();result.time=sentAt;try{archiveSent(p.number,p.text,sentAt,id);}catch(e){result.warning='SMS was sent, but local conversation history could not be saved: '+e;}}
 }else{
  result.ok=r.rc==0&&length(trim(r.out))>0&&!match(r.out+' '+error,/error|no response/i);result.message=trim(r.out+' '+error)||'No USSD response received.';
 }
 if(error&&result.ok)result.warning=error;
}catch(e){result.ok=false;result.message=''+e;}
if(!result.time)result.time=time();
writefile('/tmp/blaze-messages/'+id+'.json.new',sprintf('%J',result));rename('/tmp/blaze-messages/'+id+'.json.new','/tmp/blaze-messages/'+id+'.json');writefile('/tmp/blaze-message.json.new',sprintf('%J',result));rename('/tmp/blaze-message.json.new','/tmp/blaze-message.json');
for(let name in ['request.json','id','pid'])unlink('/tmp/blaze-message.lock/'+name);rmdir('/tmp/blaze-message.lock');
