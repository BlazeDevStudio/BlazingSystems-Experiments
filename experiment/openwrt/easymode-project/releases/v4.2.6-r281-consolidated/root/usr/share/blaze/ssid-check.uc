import {readfile} from 'fs';
import {connect} from 'ubus';
import {cursor} from 'uci';
let id=trim(readfile('/tmp/blaze-ssid-section')||''),u=cursor();
if(!id||u.get('wireless',id,'mode')!='ap')exit(1);
if(u.get('wireless',id,'disabled')=='1')exit(0);
let bus=connect(),radios=bus.call('network.wireless','status',{}),found=false;
for(let r in values(radios||{}))for(let i in r.interfaces||[])if(i.section==id&&i.ifname){try{let clients=bus.call('hostapd.'+i.ifname,'get_clients',{});if(type(clients?.clients)=='object')found=true;}catch(e){}}
bus.disconnect();exit(found?0:1);
