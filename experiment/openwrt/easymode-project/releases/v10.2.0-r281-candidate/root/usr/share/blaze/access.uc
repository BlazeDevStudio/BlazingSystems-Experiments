function profile(p){
 if(type(p)!='object'||!(p.mode in ['off','deny','allow'])||p.scope!='all')die('Choose a system-wide access policy.');
 if(type(p.macs)!='array'||length(p.macs)>128)die('Use at most 128 device MAC addresses.');
 let macs=[],seen={};for(let m in p.macs){if(type(m)!='string'||!match(m,/^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$/))die('Invalid device MAC address.');m=lc(m);if((int(substr(m,0,2),16)&1)||m=='00:00:00:00:00:00')die('Use an individual device MAC address.');if(!seen[m]){seen[m]=true;push(macs,m);}}
 if(p.mode=='allow'&&!length(macs))die('Add at least one allowed device before enabling the allowlist.');
 return {mode:p.mode,scope:'all',macs};
}
function rules(p){
 let s='add table inet blaze_access\ndelete table inet blaze_access\nadd table inet blaze_access\nadd set inet blaze_access client_macs { type ether_addr; }\n';
 if(length(p.macs))s+='add element inet blaze_access client_macs { '+join(', ',p.macs)+' }\n';
 // All local bridges, including LAN, dedicated repeater, Piso VLANs and backup LAN.
 // Input to this router is never filtered, so administration/DHCP/DNS remain available.
 s+='add chain inet blaze_access forward { type filter hook forward priority -10; policy accept; }\n';
 if(p.mode!='off')s+='add rule inet blaze_access forward iifname "br-*" ether saddr '+(p.mode=='allow'?'!= ':'')+'@client_macs counter drop\n';
 return s;
}
export {profile,rules};
