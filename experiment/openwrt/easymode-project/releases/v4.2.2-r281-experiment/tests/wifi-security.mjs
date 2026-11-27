import assert from 'node:assert/strict';
import {scanSecurity} from '../root/www/easy/core.js';
for(const [enc,expected] of [
 [{enabled:false},'none'],
 [{enabled:true,wpa:[1],authentication:['psk']},'psk'],
 [{enabled:true,wpa:[2],authentication:['psk']},'psk2'],
 [{enabled:true,wpa:[1,2],authentication:['psk']},'psk-mixed'],
 [{enabled:true,wpa:[2,3],authentication:['psk','sae']},'sae-mixed'],
 [{enabled:true,wpa:[3],authentication:['sae']},'sae'],
 [{enabled:true,wpa:[2],authentication:['eap']},'unsupported'],
 [{enabled:true,wep:['open']},'unsupported'],
 [{},'unsupported']
])assert.equal(scanSecurity({encryption:enc}).mode,expected);
console.log('PASS: open/WPA/WPA2/WPA3, mixed, enterprise and unknown scan classification');
