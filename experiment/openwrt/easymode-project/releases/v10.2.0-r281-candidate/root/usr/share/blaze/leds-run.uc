import {writefile} from 'fs';
import {config,readjson} from '/usr/share/blaze/common.uc';
import {ledSettings,ledProfile,applyLED} from '/usr/share/blaze/leds.uc';
let u=config(),save=ARGV[0]=='save',p=save?ledProfile(readjson('/tmp/blaze-led-request.json',{})):ledSettings(u);
try{
 applyLED(p,save);
 if(save){u.set('blaze','leds','leds');for(let k,v in p)u.set('blaze','leds',k,''+v);if(!u.commit('blaze'))die('LED profile commit failed.');}
}catch(e){writefile('/tmp/blaze-led.json',sprintf('%J',{time:time(),error:''+e}));die(''+e);}
