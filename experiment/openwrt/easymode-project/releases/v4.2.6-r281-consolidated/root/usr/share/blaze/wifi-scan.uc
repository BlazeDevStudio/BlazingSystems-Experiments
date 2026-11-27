import {connect} from 'ubus';
import {writefile} from 'fs';
function ubusCall(c,obj,method,args){try{return c.call(obj,method,args)||{};}catch(e){return null;}}
function wifiScan(){
 let c=connect(),out=[],seen={};if(!c)return {ok:false,error:'ubus unavailable'};
 try{
  let dr=ubusCall(c,'iwinfo','devices',{})||{},devices=type(dr.devices)=='array'?dr.devices:[];
  for(let radio in ['radio0','radio1']){
   let pr=ubusCall(c,'iwinfo','phyname',{section:radio})||{},phy=pr.phyname||'',dev='';
   if(phy){
    for(let d in devices){if(!dev){let inf=ubusCall(c,'iwinfo','info',{device:d})||{};if(inf.phy==phy)dev=d;}}
    if(dev){
     let r=ubusCall(c,'iwinfo','scan',{device:dev})||{},list=type(r.results)=='array'?r.results:[];
     for(let x in list){let ssid=''+(x.ssid||''),bssid=''+(x.bssid||''),key=bssid||radio+'|'+ssid+'|'+(x.channel||'');if(!seen[key]){seen[key]=true;let sig=int(x.signal||-100);if(sig>0&&sig>2147483647)sig-=4294967296;push(out,{radio,device:dev,ssid,bssid,channel:int(x.channel||0),signal:sig,quality:int(x.quality||0),quality_max:int(x.quality_max||70),encryption:x.encryption||{}});}}
    }
   }
  }
 }catch(e){c.disconnect();return {ok:false,error:'Wi-Fi scan failed: '+e};}
 c.disconnect();return {ok:true,networks:out,time:time()};
}
let r=wifiScan();r.id=ARGV[0];r.pending=false;print(sprintf('%J',r));
