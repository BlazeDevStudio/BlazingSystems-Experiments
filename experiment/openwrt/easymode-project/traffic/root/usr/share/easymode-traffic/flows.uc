// Isolated observation table: no accept/drop/reject/NAT rules, no acceleration changes.
import {readfile,writefile,unlink} from 'fs';
import {command,readJSON,atomic} from './runtime.uc';
function rules(wans,lans,limit) {
 let valid=a=>filter(a,x=>match(x,/^[A-Za-z0-9_.:@-]{1,32}$/));wans=valid(wans);lans=valid(lans);
 if(!length(wans)||!length(lans))return '';
 let list=a=>'{ '+join(', ',map(a,x=>'"'+x+'"'))+' }',text='table inet easymode_traffic {\n';
 for(let family in ['4','6'])for(let direction in ['upload','download'])text+='set '+direction+family+' { type ipv'+family+'_addr . ipv'+family+'_addr; flags dynamic,timeout; timeout 1h; size '+limit+'; counter; }\n';
 text+='chain observe { type filter hook forward priority -5; policy accept;\n';
 for(let family in ['4','6']) {let ip=family=='4'?'ip':'ip6';text+='iifname '+list(lans)+' oifname '+list(wans)+' update @upload'+family+' { '+ip+' saddr . '+ip+' daddr timeout 1h counter }\n';text+='iifname '+list(wans)+' oifname '+list(lans)+' update @download'+family+' { '+ip+' daddr . '+ip+' saddr timeout 1h counter }\n';}
 return text+'}\n}\n';
}
function ensureFlows(wans,lans,limit,allowed) {
 let marker=readJSON('/tmp/easymode-traffic/flow.json',{}),existing=command('nft -j list table inet easymode_traffic 2>/dev/null'),text=allowed?rules(wans,lans,limit):'';
 if(!text){if(existing)command('nft delete table inet easymode_traffic 2>/dev/null');unlink('/tmp/easymode-traffic/flow.json');return {available:false,generation:'',data:[]};}
 if(!existing||marker.rules!=text){let script=(existing?'delete table inet easymode_traffic\n':'')+text;writefile('/tmp/easymode-traffic/rules.nft',script);command('nft -f /tmp/easymode-traffic/rules.nft 2>/dev/null');existing=command('nft -j list table inet easymode_traffic 2>/dev/null');if(!existing)return {available:false,generation:'',data:[]};marker={rules:text,generation:trim(readfile('/proc/sys/kernel/random/uuid'))};atomic('/tmp/easymode-traffic/flow.json',marker);}
 let data=[];try{data=json(existing).nftables || [];}catch(e){}
 let peak=0;for(let entry in data)if(entry.set)peak=max(peak,length(entry.set.elem || []));
 return {available:true,generation:marker.generation,data,peak,capacity:limit,limited:peak>=limit};
}
function parseFlows(data,identities) {
 let flows=[];
 for(let entry in data){let s=entry.set || entry.element;if(!s || !match(s.name || '',/^(upload|download)[46]$/))continue;let direction=substr(s.name,0,6)=='upload'?'upload':'download';
  for(let el in s.elem || []) {let e=el.elem || el,pair=e.val?.concat || e.concat,counter=e.counter;if(!pair||length(pair)!=2||!counter)continue;let client=''+pair[0],remote=''+pair[1],id=identities[client] || '';
   push(flows,{key:s.name+'|'+client+'|'+remote,bytes:int(counter.bytes),client,remote,client_id:id,direction});
  }
 }
 return flows;
}
export {rules,ensureFlows,parseFlows};
