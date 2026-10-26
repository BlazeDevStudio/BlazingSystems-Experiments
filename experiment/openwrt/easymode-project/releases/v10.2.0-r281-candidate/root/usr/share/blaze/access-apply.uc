import {readfile,writefile,rename,unlink,popen} from 'fs';
import {profile,rules} from '/usr/share/blaze/access.uc';
let file='/etc/blaze/access.json',old=readfile(file),update=ARGV[0]!='--restore';
let p=profile(json(update?ARGV[0]:(old||'{"mode":"off","scope":"all","macs":[]}')));
function run(cmd){let f=popen(cmd+' 2>&1','r'),s=f.read('all'),rc=f.close();if(rc)die(s);return s;}
if(p.mode!='off'&&trim(run("uci -q get firewall.@defaults[0].flow_offloading || true"))=='1')die('Disable firewall flow offloading in LuCI before enabling device filtering.');
function apply(v){writefile('/tmp/blaze-access.nft',rules(v));run('nft -c -f /tmp/blaze-access.nft');run('nft -f /tmp/blaze-access.nft');}
apply(p);
if(update){
 try{if(writefile(file+'.new',sprintf('%J',p))==null||!rename(file+'.new',file))die('Could not save access policy.');}
 catch(e){apply(profile(json(old||'{"mode":"off","scope":"all","macs":[]}')));unlink(file+'.new');die(e);}
}
unlink('/tmp/blaze-access.nft');print('Internet access policy applied.\n');
