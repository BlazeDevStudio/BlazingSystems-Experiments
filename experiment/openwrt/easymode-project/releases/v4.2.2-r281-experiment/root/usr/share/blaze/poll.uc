import {writefile,rename} from 'fs';
import {radio,readjson} from '/usr/share/blaze/common.uc';
let current=radio(),previous=readjson('/tmp/blaze-radio.json',{});
if(!current.available&&previous.available){previous.stale=true;previous.last_attempt=time();previous.last_error=current.error||'';current=previous;}
else{current.stale=!current.available;current.last_attempt=time();}
writefile('/tmp/blaze-radio.json.new',sprintf('%J',current));rename('/tmp/blaze-radio.json.new','/tmp/blaze-radio.json');
