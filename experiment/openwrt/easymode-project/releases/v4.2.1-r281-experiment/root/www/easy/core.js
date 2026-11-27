export function normalizePhone(number,mccmnc){
  const s=String(number??'').trim().replace(/[ ()-]/g,'');
  if(!/^\+?\d{3,15}$/.test(s))throw new Error('Enter 3–15 digits, optionally starting with +.');
  return String(mccmnc??'').startsWith('515')&&/^0\d{10}$/.test(s)?'63'+s.slice(1):s.replace(/^\+/,'');
}
export function inboxMessages(data){
  const messages=Array.isArray(data)?data:data?.msg;
  if(!Array.isArray(messages))throw new Error('Unexpected modem inbox format. Refresh or check Advanced SMS.');
  return messages;
}
export function canonicalSmsPeer(value){
  const raw=String(value??'').trim();
  const compact=raw.replace(/[ ()-]/g,'').replace(/^\+/,'');
  if(/^0\d{10}$/.test(compact))return '63'+compact.slice(1);
  return /^\d{3,15}$/.test(compact)?compact:(raw||'Unknown');
}
export function smsTimeValue(value){
  if(typeof value==='number'&&Number.isFinite(value))return value>1e11?value:value*1000;
  if(/^\d+$/.test(String(value||''))){const n=Number(value);return n>1e11?n:n*1000;}
  const s=String(value||'').trim();if(!s)return 0;
  const local=/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(s)?s.replace(' ','T'):s;
  const t=Date.parse(local);return Number.isFinite(t)?t:0;
}
export function mergeInboxMessages(data){
  const source=inboxMessages(data),groups=new Map(),plain=[];
  for(const raw of source){
    const sender=canonicalSmsPeer(raw.sender||raw.number||raw.from),timestamp=raw.timestamp||raw.date||'',text=String(raw.content??raw.message??raw.text??'');
    const total=Number(raw.total||raw.parts||raw.concat_total)||0,part=Number(raw.part||raw.sequence||raw.concat_part)||0,index=String(raw.index??'');
    const reference=String(raw.reference??raw.ref??raw.concat_ref??raw.concat_reference??'');
    if(total>1){
      const key=reference?`${sender}\u0000ref:${reference}\u0000${total}`:`${sender}\u0000${timestamp}\u0000${total}`;
      let g=groups.get(key);if(!g){g={sender,timestamp,total,parts:{},indexes:[]};groups.set(key,g);}
      g.parts[part||Object.keys(g.parts).length+1]=text;if(index)g.indexes.push(index);
    }else plain.push({direction:'in',peer:sender,text,timestamp,time:smsTimeValue(timestamp),index,status:raw.status||raw.state||''});
  }
  for(const g of groups.values()){
    const text=Object.keys(g.parts).map(Number).sort((a,b)=>a-b).map(k=>g.parts[k]).join('');
    plain.push({direction:'in',peer:g.sender,text,timestamp:g.timestamp,time:smsTimeValue(g.timestamp),index:g.indexes.join('-'),status:''});
  }
  return plain.sort((a,b)=>a.time-b.time);
}
export function buildSmsThreads(incoming=[],sent=[]){
  const map=new Map();
  const add=m=>{const peer=canonicalSmsPeer(m.peer||m.number||m.sender);if(!map.has(peer))map.set(peer,[]);map.get(peer).push({...m,peer,time:smsTimeValue(m.time||m.timestamp)});};
  incoming.forEach(add);sent.forEach(m=>add({direction:'out',peer:m.number,text:m.text,time:m.time,timestamp:m.timestamp||'',status:m.status||'sent',id:m.id||''}));
  const threads=[];
  for(const [peer,messages] of map){messages.sort((a,b)=>a.time-b.time);threads.push({peer,messages,last:messages[messages.length-1],lastTime:messages[messages.length-1]?.time||0});}
  return threads.sort((a,b)=>b.lastTime-a.lastTime);
}
export function smsTextInfo(text){
  const s=String(text??'');let units=0,valid=true;
  for(const c of s){const n=c.codePointAt(0);if((n<32&&n!==10&&n!==13)||n>126||n===96)valid=false;units+='^{}\\[~]|'.includes(c)?2:1;}
  return {units,remaining:160-units,valid,segments:units?Math.ceil(units/160):0};
}
export function activeCarriers(radio){return (radio?.carriers||[]).filter(c=>c.active!==false&&Number(c.band)>0);}
export function normalizeBandCaps(raw={}){
  const clean=a=>Array.isArray(a)?a.map(x=>typeof x==='number'?{band:x,txt:''}:{band:Number(x?.band),txt:String(x?.txt||'')}).filter(x=>Number.isInteger(x.band)&&x.band>0):[];
  const ints=a=>Array.isArray(a)?a.map(Number).filter(x=>Number.isInteger(x)&&x>0):[];
  return {
    modem:String(raw.modem||''),error:String(raw.error||''),
    lte:{supported:clean(raw.supported),enabled:ints(raw.enabled)},
    nsa:{supported:clean(raw.supported5gnsa),enabled:ints(raw.enabled5gnsa)},
    sa:{supported:clean(raw.supported5gsa),enabled:ints(raw.enabled5gsa)}
  };
}
export function bandTitle(item,rat='lte'){
  const p=rat==='lte'?'B':'n',n=Number(item?.band)||0,t=String(item?.txt||'').trim();
  return {name:`${p}${n}`,detail:t||'Supported by modem'};
}
export function portLabel(device){return {wan:'LAN1 / WAN',lan3:'LAN2',lan2:'LAN3',lan1:'LAN4'}[device]||device;}
export function trialDecision({before,after,online,requireCA,ca}){return online&&before>0&&after>=before&&(!requireCA||ca)?'keep':'rollback';}

export function scanSecurity(n){
 const e=n?.encryption||{},auth=(Array.isArray(e.authentication)?e.authentication:[]).map(x=>String(x).toLowerCase()),wpa=(Array.isArray(e.wpa)?e.wpa:[]).map(Number);
 if(e.enabled===false)return {mode:'none',label:'Open'};
 if(auth.includes('eap')||auth.includes('802.1x'))return {mode:'unsupported',label:'Enterprise / manual setup'};
 if(auth.includes('sae'))return auth.includes('psk')?{mode:'sae-mixed',label:'WPA2/WPA3'}:{mode:'sae',label:'WPA3'};
 if(auth.includes('psk')){
  if(wpa.includes(1)&&wpa.includes(2))return {mode:'psk-mixed',label:'WPA/WPA2'};
  if(wpa.includes(2))return {mode:'psk2',label:'WPA2'};
  if(wpa.includes(1))return {mode:'psk',label:'WPA'};
 }
 return {mode:'unsupported',label:'Unsupported / unknown security'};
}
