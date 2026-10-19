// Monotonic observed-presence accounting; no traffic or browsing history.
function advance(old,observations,epoch,up,boot){
 let devices=old.devices||{},same=old.boot==boot,dt=same?up-int(old.uptime):-1,continuous=dt>=0&&dt<=90;
 let observed={};for(let o in observations){let mac=lc(o.mac||'');if(match(mac,/^([0-9a-f]{2}:){5}[0-9a-f]{2}$/))observed[mac]=o;}
 for(let mac,o in observed)if(!devices[mac])devices[mac]={mac,total_seconds:0,session_seconds:0,history:[],online:false};
 for(let mac,d in devices){
  let o=observed[mac]||{};
  if(o.name&&o.name!='Unnamed')d.name=substr(o.name,0,128);
  if(o.ip)d.ip=substr(o.ip,0,64);
  let present=o.online===true;
  // Only wired/recent-neighbour observations get a short idle grace period.
  if(!present&&continuous&&d.online&&d.medium=='LAN'&&up-int(d.seen_uptime)<=180)present=true;
  if(d.online&&(!present||!continuous)){
   unshift(d.history,{start:d.session_start,end:old.time,seconds:d.session_seconds,reason:!same?'Router restarted':!continuous?'Observation gap':'Not recently seen'});
   d.history=slice(d.history,0,8);d.online=false;d.session_seconds=0;
  }
  if(present){
   if(!d.online){d.session_start=epoch;d.session_seconds=0;d.online=true;}
   else{d.session_seconds+=dt;d.total_seconds+=dt;}
   if(o.online){d.last_seen=epoch;d.seen_uptime=up;d.medium=o.medium||'LAN';d.interface=o.interface||'';}
  }
  d.total_seconds=max(0,int(d.total_seconds));
 }
 let order=sort(keys(devices),(a,b)=>int(devices[b].online)-int(devices[a].online)||int(devices[b].last_seen)-int(devices[a].last_seen));
 for(let i=128;i<length(order);i++)delete devices[order[i]];
 return {schema:1,boot,time:epoch,uptime:up,started:old.started||epoch,devices,checkpoint:old.checkpoint||0};
}
export {advance};
