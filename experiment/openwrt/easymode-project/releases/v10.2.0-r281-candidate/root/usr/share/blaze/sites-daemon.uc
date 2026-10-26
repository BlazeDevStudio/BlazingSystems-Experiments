import * as socket from 'socket';
import * as loop from 'uloop';
import {readfile,writefile,popen} from 'fs';
import {profile,denied,question,response,answerNames,word} from '/usr/share/blaze/sites.uc';
let cfg=profile(json(readfile(ARGV[0]||'/etc/blaze/sites.json')||'{"enabled":false,"mode":"off","domains":[],"devices":[]}'));
let base=int(ARGV[1]||1053),listeners=[],pending={},peers={},serial=0,stats={started:time(),queries:0,blocked:0,errors:0};
// Bind the same local addresses used by DNAT so UDP replies retain their
// source address even when the client is on another bridge/subnet.
let f=popen("ubus call network.interface.lan status",'r'),lan=json(f.read('all'));f.close();
let addresses=[{family:socket.AF_INET,address:lan['ipv4-address'][0].address}];
for(let line in split(readfile('/proc/net/if_inet6')||'','\n')){let cols=split(trim(line),/\s+/);if(cols[5]=='br-lan'&&cols[3]=='00'&&match(cols[0],/^[0-9a-f]{32}$/)){let groups=[];for(let i=0;i<32;i+=4)push(groups,substr(cols[0],i,4));push(addresses,{family:socket.AF_INET6,address:join(':',groups)});break;}}
loop.init();
function closeItem(pool,id){let x=pool[id];if(!x)return;x.h?.delete();x.s.close();delete pool[id];}
function replyTCP(id,data){let p=peers[id];if(!p)return;p.h?.delete();p.out=chr(length(data)>>8)+chr(length(data)&255)+data;p.h=loop.handle(p.s,()=>{let n=p.s.send(p.out);if(n==null){closeItem(peers,id);return;}p.out=substr(p.out,n);if(!length(p.out))closeItem(peers,id);},loop.ULOOP_WRITE);}
function resolve(data,policy,send,tcp){
 let q;try{q=question(data);if(q.klass!=1||q.type==255)die('unsupported');}catch(e){stats.errors++;return;}
 stats.queries++;
 if(denied(policy,q.name)){stats.blocked++;send(response(data,5));return;}
 if(length(keys(pending))>=64){stats.errors++;send(response(data,2));return;}
 let s=socket.create(socket.AF_INET,(tcp?socket.SOCK_STREAM:socket.SOCK_DGRAM)|socket.SOCK_NONBLOCK);
 if(!s){stats.errors++;send(response(data,2));return;}
 // Only forward to the existing local resolver; never expose a remote proxy.
 s.connect({address:'127.0.0.1',port:53});
 let id=++serial,x={s,h:null,until:time()+5,buf:'',out:tcp?chr(length(data)>>8)+chr(length(data)&255)+data:data};pending[id]=x;
 function finish(answer){closeItem(pending,id);try{if(substr(answer,0,2)!=substr(data,0,2)||!(ord(answer,2)&128)||word(answer,4)!=1)die('bad upstream');let names=answerNames(answer);for(let name in names)if(denied(policy,name)){stats.blocked++;send(response(data,5));return;}send(answer);}catch(e){stats.errors++;send(response(data,2));}}
 x.h=loop.handle(s,()=>{let n=s.send(x.out);if(n==null){closeItem(pending,id);stats.errors++;send(response(data,2));return;}x.out=substr(x.out,n);if(length(x.out))return;x.h.delete();x.h=loop.handle(s,()=>{let b=s.recv(4098);if(b==null)return;if(!length(b)){closeItem(pending,id);return;}if(!tcp){finish(b);return;}x.buf+=b;if(length(x.buf)>4098){closeItem(pending,id);send(response(data,2));return;}if(length(x.buf)>=2&&length(x.buf)>=word(x.buf,0)+2)finish(substr(x.buf,2,word(x.buf,0)));},loop.ULOOP_READ);},loop.ULOOP_WRITE);
}
function listenOne(policy,port,tcp,bind){
  let s=socket.create(bind.family,(tcp?socket.SOCK_STREAM:socket.SOCK_DGRAM)|socket.SOCK_NONBLOCK);
  if(!s)die('DNS socket unavailable');s.setopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);if(bind.family==socket.AF_INET6)s.setopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,1);
  if(!s.bind({address:bind.address,port}))die('DNS listener bind failed');if(tcp&&!s.listen(16))die('DNS listen failed');
  let h=loop.handle(s,()=>{
   if(!tcp){let addr={},data=s.recv(4097,0,addr);if(data!=null)resolve(data,policy,r=>s.send(r,0,addr),false);return;}
   let addr={},peer=s.accept(addr,socket.SOCK_NONBLOCK);if(!peer)return;if(length(keys(peers))>=32){peer.close();return;}
   let id=++serial,p={s:peer,h:null,until:time()+7,buf:''};peers[id]=p;
   p.h=loop.handle(peer,()=>{let b=peer.recv(4098);if(b==null)return;if(!length(b)){closeItem(peers,id);return;}p.buf+=b;if(length(p.buf)>4098){closeItem(peers,id);return;}if(length(p.buf)<2)return;let size=word(p.buf,0);if(size<12||size>4096){closeItem(peers,id);return;}if(length(p.buf)<size+2)return;p.h.delete();p.h=null;resolve(substr(p.buf,2,size),policy,r=>replyTCP(id,r),true);},loop.ULOOP_READ);
  },loop.ULOOP_READ);push(listeners,{s,h});
}
function listen(policy,port){for(let bind in addresses){listenOne(policy,port,false,bind);listenOne(policy,port,true,bind);}}
listen(cfg,base);for(let i=0;i<length(cfg.devices);i++)listen(cfg.devices[i],base+i+1);
let tick;tick=loop.timer(1000,function(){for(let id,x in pending)if(x.until<=time()){closeItem(pending,id);stats.errors++;}for(let id,x in peers)if(x.until<=time())closeItem(peers,id);stats.time=time();stats.pending=length(keys(pending));writefile('/tmp/blaze-sites-status.json',sprintf('%J',stats));tick.set(1000);});
loop.run();
