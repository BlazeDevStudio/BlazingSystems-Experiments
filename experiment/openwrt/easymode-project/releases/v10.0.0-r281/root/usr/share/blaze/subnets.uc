function ipv4(raw){let a=split(''+raw,'.'),n=0;if(length(a)!=4)die('Invalid IPv4 address');for(let x in a){if(!match(x,/^[0-9]+$/)||int(x)>255)die('Invalid IPv4 address');n=(n<<8)|int(x);}return n;}
function mask(prefix){prefix=int(prefix);if(prefix<0||prefix>32)die('Invalid IPv4 prefix');return prefix==0?0:(0xffffffff<<(32-prefix))&0xffffffff;}
function netmask(raw){return index(''+raw,'.')>=0?ipv4(raw):mask(raw);}
function overlaps(a,am,b,bm){let an=ipv4(a),bn=ipv4(b),ma=netmask(am),mb=netmask(bm);return (an&ma)==(bn&ma)||(an&mb)==(bn&mb);}
export {ipv4,mask,overlaps};
