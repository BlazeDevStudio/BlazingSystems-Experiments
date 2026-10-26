import {readfile,writefile,rename,unlink,popen} from 'fs';
import {profile} from '/usr/share/blaze/sites.uc';
let p=profile(json(ARGV[0])),file='/etc/blaze/sites.json',old=readfile(file)||'{"enabled":false,"mode":"off","domains":[],"devices":[]}';
function restart(){let f=popen('/etc/init.d/blaze-sites restart 2>&1','r'),s=f.read('all'),rc=f.close();if(rc)die(s);}
if(writefile(file+'.new',sprintf('%J',p))==null||!rename(file+'.new',file))die('Could not save site policy.');
try{restart();}catch(e){writefile(file,old);try{restart();}catch(ignored){}die('Site policy was not activated; previous configuration restored: '+e);}
writefile(file+'.before',old);print('Site DNS policy applied.\n');
