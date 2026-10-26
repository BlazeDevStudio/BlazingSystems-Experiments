// Domain policies and bounded DNS parsing; no URL/content inspection.
function profile(p){
 if(type(p)!='object'||type(p.enabled)!='bool'||!(p.mode in ['off','deny','allow']))die('Invalid site policy.');
 function domains(a){if(type(a)!='array'||length(a)>128)die('Use up to 128 domains per policy.');let out=[];for(let d in a){if(type(d)!='string')die('Invalid domain.');d=lc(trim(d));d=replace(d,/^\*\./,'');d=replace(d,/\.$/,'');if(length(d)>253||!match(d,/^[a-z0-9][a-z0-9.-]*\.[a-z][a-z0-9-]*$/))die('Enter domain names only, without URLs or paths.');for(let l in split(d,'.'))if(!length(l)||length(l)>63||substr(l,0,1)=='-'||substr(l,-1)=='-')die('Invalid domain label.');if(!(d in out))push(out,d);}return out;}
 let out={enabled:p.enabled,mode:p.mode,domains:domains(p.domains||[]),devices:[]},seen={};
 if(type(p.devices||[])!='array'||length(p.devices||[])>32)die('Use up to 32 device overrides.');
 for(let d in p.devices||[]){let m=lc(d.mac||'');if(!match(m,/^([0-9a-f]{2}:){5}[0-9a-f]{2}$/)||(int(substr(m,0,2),16)&1)||m=='00:00:00:00:00:00'||seen[m])die('Invalid or duplicate device MAC.');if(!(d.mode in ['off','deny','allow']))die('Invalid device mode.');seen[m]=true;push(out.devices,{mac:m,mode:d.mode,domains:domains(d.domains||[])});}
 let count=length(out.domains);for(let d in out.devices)count+=length(d.domains);if(count>512)die('Use at most 512 domain entries in total.');return out;
}
function effective(p,mac){if(!p.enabled)return {mode:'off',domains:[]};for(let d in p.devices)if(d.mac==mac)return d;return p;}
function matches(name,domains){name=lc(name);for(let d in domains)if(name==d||(length(name)>length(d)&&substr(name,-length(d)-1)=='.'+d))return true;return false;}
function denied(p,name){return p.mode=='deny'?matches(name,p.domains):p.mode=='allow'?!matches(name,p.domains):false;}
function word(s,n){if(n+2>length(s))die('Short DNS message');return ord(s,n)*256+ord(s,n+1);}
function nameAt(s,n){let labels=[],end=null,hops=0,seen={};while(true){if(n>=length(s)||hops++>128||seen[n])die('Invalid DNS name');seen[n]=true;let l=ord(s,n++);if((l&192)==192){if(n>=length(s))die('Short pointer');let ptr=((l&63)<<8)|ord(s,n++);if(end==null)end=n;n=ptr;continue;}if(l&192||l>63||n+l>length(s))die('Invalid label');if(!l)break;push(labels,substr(s,n,l));n+=l;}let name=lc(join('.',labels));if(length(name)>253)die('Long DNS name');return {name,end:end==null?n:end};}
function question(s){if(length(s)<12||length(s)>4096||word(s,4)!=1||(ord(s,2)&248))die('Unsupported DNS query');let q=nameAt(s,12);return {name:q.name,type:word(s,q.end),klass:word(s,q.end+2),end:q.end+4};}
function response(s,code){let q=question(s);return substr(s,0,2)+chr(128|(ord(s,2)&1))+chr(128|code)+substr(s,4,2)+'\x00\x00\x00\x00\x00\x00'+substr(s,12,q.end-12);}
function answerNames(s){let n=12,names=[];for(let i=0;i<word(s,4);i++)n=nameAt(s,n).end+4;let count=word(s,6)+word(s,8)+word(s,10);if(count>256)die('Too many records');for(let i=0;i<count;i++){let q=nameAt(s,n);n=q.end;let t=word(s,n),size=word(s,n+8);n+=10;if(n+size>length(s))die('Short record');if(t==5||t==39)push(names,nameAt(s,n).name);n+=size;}return names;}
export {profile,effective,matches,denied,question,response,answerNames,word};
