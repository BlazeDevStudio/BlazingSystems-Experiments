// Pure accounting. UTC day buckets; byte counters are never inferred from link rates.
function delta(previous, current, same, bits) {
 if (!same || type(previous) != 'int' || type(current) != 'int' || current < 0) return 0;
 if (current >= previous) return current - previous;
 // Wrap only for a collector explicitly reporting a 32-bit counter near its boundary.
 if (bits == 32 && previous > 4026531840 && current < 268435456) return 4294967296 - previous + current;
 return 0;
}
function uniqueWAN(interfaces, overrides, edition) {
 let out = {}, names = {};
 if (edition in ['ap', 'switch']) return [];
 for (let i in interfaces || []) {
  let wan = length(overrides || []) ? i.interface in overrides : false;
  if (!length(overrides || [])) for (let r in i.route || []) if ((r.target == '0.0.0.0' || r.target == '::') && int(r.mask) == 0) wan = true;
  if (!wan || !i.up || !match(i.l3_device || '', /^[A-Za-z0-9_.:@-]{1,32}$/)) continue;
  let d = i.l3_device;
  if (!out[d]) out[d] = {device:d, interfaces:[], uptime:i.uptime || 0, proto:i.proto || '', up:true};
  push(out[d].interfaces, i.interface); names[i.interface] = d;
 }
 return values(out);
}
function appFor(domain) {
 // Only brand-specific hostnames are mapped. Shared CDNs remain unknown or
 // provider-level services; a DNS query never proves that an app was opened.
 let rules = {
  'youtube.com':'YouTube','googlevideo.com':'YouTube','ytimg.com':'YouTube',
  'facebook.com':'Facebook','messenger.com':'Messenger','fbcdn.net':'Meta services',
  'instagram.com':'Instagram','cdninstagram.com':'Instagram',
  'tiktok.com':'TikTok','tiktokcdn.com':'TikTok','tiktokv.com':'TikTok',
  'netflix.com':'Netflix','nflxvideo.net':'Netflix','nflximg.net':'Netflix',
  'spotify.com':'Spotify','scdn.co':'Spotify',
  'discord.com':'Discord','discord.gg':'Discord','discordapp.net':'Discord',
  'whatsapp.com':'WhatsApp','whatsapp.net':'WhatsApp',
  'telegram.org':'Telegram','t.me':'Telegram',
  'steampowered.com':'Steam','steamcontent.com':'Steam','steamstatic.com':'Steam',
  'roblox.com':'Roblox','rbxcdn.com':'Roblox',
  'epicgames.com':'Epic Games','zoom.us':'Zoom','zoom.com':'Zoom',
  'teams.microsoft.com':'Microsoft Teams',
  'twitter.com':'X','x.com':'X','twimg.com':'X',
  'reddit.com':'Reddit','redd.it':'Reddit',
  'chatgpt.com':'ChatGPT','openai.com':'OpenAI services','claude.ai':'Claude',
  'dropbox.com':'Dropbox','signal.org':'Signal',
  'windowsupdate.com':'Software updates','update.microsoft.com':'Software updates'
 };
 for (let suffix, app in rules) if (domain == suffix || substr(domain, -length(suffix)-1) == '.'+suffix) return app;
 return 'Unknown applications';
}
function observeDNS(old, lines, now, limit) {
 let queries = {}, bindings = {}, observations = old.observations || {};
 for (let line in lines) {
  let m = match(line, /\s([0-9]+) ([0-9a-fA-F:.]+)\/[0-9]+ (.+)$/);
  if (!m) continue;
  let serial=m[1], client=lc(m[2]), text=m[3], q=match(text,/^query\[(A|AAAA)\] ([a-zA-Z0-9_.-]{1,253}) from /);
  if (q) { let domain=lc(q[2]); queries[serial]={client, domain}; let key=client+'|'+domain; observations[key]={client,domain,first:observations[key]?.first || now,last:now,confidence:'Observed domain — not proof of a visit'}; }
  let r=match(text,/^(reply|cached) ([a-zA-Z0-9_.-]+) is ([0-9a-fA-F:.]+)$/), query=queries[serial];
  if (r && query && match(r[3],/[.:]/)) {let key=query.client+'|'+lc(r[3]); if(!bindings[key])bindings[key]={domains:{},expires:now+60}; bindings[key].domains[query.domain]=true;}
 }
 // Retain only short-lived associations; repeated lines are never counted as bytes.
 for(let o in values(observations))o.service=appFor(o.domain);
 for(let key,b in old.bindings || {}) if(b.expires>now) {if(!bindings[key])bindings[key]=b;else for(let d in keys(b.domains))bindings[key].domains[d]=true;}
 let order=sort(keys(observations),(a,b)=>observations[b].last-observations[a].last);
 for(let n=limit;n<length(order);n++)delete observations[order[n]];
 // Bound retained IP associations independently of DNS query volume. Dropping
 // whole bindings leaves traffic unknown instead of inventing a unique match.
 let addresses=sort(keys(bindings),(a,b)=>bindings[b].expires-bindings[a].expires);
 for(let n=limit;n<length(addresses);n++)delete bindings[addresses[n]];
 return {observations,bindings};
}
function attribution(dns, client, remote, now) {
 let b=dns?.bindings?.[client+'|'+remote], ds=keys(b?.domains || {});
 if (!b || b.expires < now || length(ds)!=1) return {domain:'Other/Unknown',app:'Unknown applications',confidence:length(ds)>1?'Ambiguous/shared address':'Unknown traffic'};
 return {domain:ds[0],app:appFor(ds[0]),confidence:'Estimated attribution — DNS and flow association'};
}
function add(map,key,down,up) { if(!map[key])map[key]={download:0,upload:0}; map[key].download+=down; map[key].upload+=up; }
function advance(old, sample, cfg) {
 let dt=sample.monotonic-int(old.monotonic || 0), same=old.boot==sample.boot && dt>0 && dt<=max(120,cfg.interval*4), day=''+int(sample.time/86400);
 let state={schema:1,boot:sample.boot,time:sample.time,monotonic:sample.monotonic,started:old.started || sample.time,checkpoint:old.checkpoint || 0,previous:{},flows:{},days:old.days || {},devices:old.devices || {},domains:old.domains || {},events:old.events || [],live:old.live || [],wan:[],wifi:sample.wifi || [],system:sample.system || {},capabilities:sample.capabilities || {},dns:sample.dns || {observations:{},bindings:{}},coverage:'Observed counters; collection gaps are not backfilled',interval:cfg.interval};
 state.totals=old.totals || {wan:{}};state.recent=old.recent || {};let slot=''+int(sample.time/300);if(!state.recent[slot])state.recent[slot]={wan:{}};
 state.activity=old.activity || {};
 function activity(client,domain,kind,stamp){
  if(!client || domain=='Other/Unknown')return;
  let key=client+'|'+domain,a=state.activity[key] || {client_id:client,domain,first:stamp,last_dns:0,last_flow:0};a.app=appFor(domain);
  a[kind]=max(a[kind] || 0,stamp);state.activity[key]=a;
 }
 if(cfg.domains)for(let o in values(sample.dns?.observations || {}))if(o.client_id)activity(o.client_id,o.domain,'last_dns',o.last);
 if(!state.days[day])state.days[day]={wan:{},devices:{},domains:{},apps:{}};
 let bucket=state.days[day], download=0,upload=0;
 for(let w in sample.wan || []) {
  let p=old.previous?.[w.device], continuous=same && p?.identity==w.identity;
  let down=delta(p?.rx,w.rx,continuous,w.bits),up=delta(p?.tx,w.tx,continuous,w.bits);
  state.previous[w.device]={rx:w.rx,tx:w.tx,identity:w.identity}; add(bucket.wan,w.device,down,up);add(state.recent[slot].wan,w.device,down,up);add(state.totals.wan,w.device,down,up); download+=down;upload+=up;
  push(state.wan,{...w,download_bps:same?down*8/dt:0,upload_bps:same?up*8/dt:0,observed_download:bucket.wan[w.device].download,observed_upload:bucket.wan[w.device].upload});
 }
 let before=join(',',sort(keys(old.previous || {}))), after=join(',',sort(keys(state.previous)));
 if(old.time && before!=after) {push(state.events,{time:sample.time,type:'WAN availability changed',before,after});state.events=slice(state.events,-64);}
 for(let d in values(state.devices)) {d.online=false;d.download_bps=0;d.upload_bps=0;}
 for(let d in sample.clients || []) {
  // MACs identify observed network identities, not permanent people or hardware.
  let id=lc(d.mac || '');if(!match(id,/^([0-9a-f]{2}:){5}[0-9a-f]{2}$/))continue;
  state.devices[id]={...(state.devices[id] || {download:0,upload:0,first_seen:sample.time}),...d,id,last_seen:d.online?sample.time:state.devices[id]?.last_seen || sample.time};
 }
 for(let f in sample.flows || []) {
  let p=old.flows?.[f.key], continuous=same && old.capabilities?.flow_generation==sample.capabilities?.flow_generation;
  let count=delta(p?.bytes,f.bytes,continuous,64);
  // A new element in our continuously observed table starts at zero.
  if(continuous && !p && old.time)count=f.bytes;
  if(p && p.client_id!=null && p.client_id!=f.client_id)count=0;
  state.flows[f.key]={bytes:f.bytes,client_id:f.client_id};
  let d=state.devices[f.client_id],down=f.direction=='download'?count:0,up=f.direction=='upload'?count:0;
  if(d){d.download+=down;d.upload+=up;d.download_bps+=(same?down*8/dt:0);d.upload_bps+=(same?up*8/dt:0);add(bucket.devices,d.id,down,up);}
  let a=cfg.domains?attribution(sample.dns,f.client,f.remote,sample.time):{domain:'Other/Unknown',app:'Unknown applications',confidence:'Domain observation disabled'};
  add(bucket.domains,a.domain,down,up);add(bucket.apps,a.app,down,up);
  if(count>0 && cfg.domains)activity(f.client_id,a.domain,'last_flow',sample.time);
  if(count>0 && cfg.domains && a.domain!='Other/Unknown') {let info=state.domains[a.domain] || {first:sample.time,clients:{},download:0,upload:0};info.last=sample.time;info.download+=down;info.upload+=up;info.confidence=a.confidence;info.service=a.app;if(d && (info.clients[d.id] || length(keys(info.clients))<cfg.limit))info.clients[d.id]=true;state.domains[a.domain]=info;}
 }
 let order=sort(keys(state.days),(a,b)=>int(b)-int(a));for(let i=cfg.retention;i<length(order);i++)delete state.days[order[i]];
 for(let key in keys(state.recent))if(int(key)<int(slot)-288)delete state.recent[key];
 for(let kind in ['devices','domains']) {let ids=sort(keys(state[kind]),(a,b)=>int(state[kind][b].last_seen || state[kind][b].last)-int(state[kind][a].last_seen || state[kind][a].last));for(let i=0;i<length(ids);i++)if(i>=cfg.limit||int(state[kind][ids[i]].last_seen || state[kind][ids[i]].last)<sample.time-cfg.retention*86400)delete state[kind][ids[i]];}
 for(let key,o in state.dns.observations || {})if(o.last<sample.time-cfg.retention*86400)delete state.dns.observations[key];
 let recentActivity=sort(keys(state.activity),(a,b)=>max(state.activity[b].last_dns,state.activity[b].last_flow)-max(state.activity[a].last_dns,state.activity[a].last_flow));
 for(let i=0;i<length(recentActivity);i++){let key=recentActivity[i],a=state.activity[key];if(i>=cfg.limit*2 || max(a.last_dns,a.last_flow)<sample.time-cfg.retention*86400)delete state.activity[key];}
 for(let b in values(state.days))for(let kind in ['devices','domains','apps']){let ids=sort(keys(b[kind]),(a,z)=>b[kind][z].download+b[kind][z].upload-b[kind][a].download-b[kind][a].upload);for(let i=cfg.limit;i<length(ids);i++){let id=ids[i];if(id=='Other/Unknown')continue;add(b[kind],'Other/Unknown',b[kind][id].download,b[kind][id].upload);delete b[kind][id];}}
 for(let d in values(state.devices)){d.live=d.live || [];push(d.live,{time:sample.time,download_bps:d.download_bps || 0,upload_bps:d.upload_bps || 0});d.live=slice(d.live,-30);}
 push(state.live,{time:sample.time,download_bps:same?download*8/dt:0,upload_bps:same?upload*8/dt:0});state.live=slice(state.live,-120);
 if(!cfg.domains){state.activity={};state.dns={observations:{},bindings:{}};state.domains={};for(let b in values(state.days)){b.domains={};b.apps={};}}
 return state;
}

export {delta, uniqueWAN, appFor, observeDNS, attribution, advance};
