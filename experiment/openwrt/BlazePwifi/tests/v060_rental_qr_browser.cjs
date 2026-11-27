// Node-only DOM stub validates REAL admin/rental.js async QR handling.
// No browser DOM, source mapping, network, account records or private tokens.
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const js=fs.readFileSync(path.join(__dirname,'../openwrt/rootfs/www/blazepwifi/admin/rental.js'),'utf8');
const qrSource=fs.readFileSync(path.join(__dirname,'../openwrt/rootfs/www/blazepwifi/vendor/qrcode/qrcode.js'),'utf8');
const decoderDirectory=path.join(__dirname,'vendor/jsqr-1.4.0');
const decoderProvenance=require(path.join(decoderDirectory,'PROVENANCE.json'));
assert.equal(decoderProvenance.version,'1.4.0');
for(const [filename,expected] of Object.entries(decoderProvenance.files)){
 const bytes=fs.readFileSync(path.join(decoderDirectory,filename));
 assert.equal(bytes.length,expected.bytes,`decoder ${filename} byte length changed`);
 assert.equal(createHash('sha256').update(bytes).digest('hex'),expected.sha256,`decoder ${filename} differs from pinned upstream bytes`);
}
const jsQR=require(path.join(decoderDirectory,'jsQR.js'));
class FakeClassList{
 constructor(){this.set=new Set(['hidden']);}
 add(s){this.set.add(s);}
 remove(s){this.set.delete(s);}
 contains(s){return this.set.has(s);}
}
const nodes=new Map();
for(const name of ['addRentalModal','addRentalServer','addRentalLabel','qrResult','qrBox','qrNotice','qrMeta','qrToken','qrReveal']){
 nodes.set('#'+name,{value:'',textContent:'',innerHTML:'',classList:new FakeClassList(),hidden:true,onclick:null});
}
let rendererCount=0, calls=0, resolveApi, alerts=[], requests=[], failureStage='', lastSymbol;
const fake={
 window:{BlazeCore:{
   api:(action,body)=>{calls++;requests.push({action,body:{...body}});return new Promise(resolve=>{resolveApi=resolve;});},
   toast:(msg,bad)=>alerts.push({msg,bad})
 }},
 location:{origin:'https://192.168.1.1:8443'},
 document:{querySelector:(sel)=>nodes.get(sel)||null},
 CSS:{escape:s=>s},
 setTimeout:()=>{},
 confirm:()=>true,
 console
};
const context=vm.createContext(fake);
vm.runInContext(qrSource,context,{timeout:3000});
const encoder=fake.qrcode;
// Preserve the real encoder and its static converter properties. The proxy
// exposes completed symbols and injects renderer failures without replacing QR
// encoding, its module matrix, or its generated SVG.
fake.qrcode=new Proxy(encoder,{apply(target,receiver,args){
 if(failureStage==='factory')throw new Error('injected factory failure');
 const symbol=Reflect.apply(target,receiver,args);
 lastSymbol=symbol;
 for(const stage of ['addData','make','createSvgTag']){
  const method=symbol[stage];
  symbol[stage]=(...values)=>{
   if(stage==='addData')assert.equal(typeof values[0],'string');
   if(failureStage===stage)throw new Error('injected '+stage+' failure');
   const result=Reflect.apply(method,symbol,values);
   if(stage==='createSvgTag')rendererCount++;
   return result;
  };
 }
 return symbol;
}});
vm.runInContext(js,context,{timeout:3000});
const get=n=>nodes.get('#'+n);
const qr=fake.window.BlazeRental;
const unmanaged={ok:true,qr_type:'binding',qr_payload:JSON.stringify({
 server_url:fake.location.origin, enrollment_token:'one-time-bind',
 device_name:'Fixture phone',server_cert_sha256:''}),
 enrollment_token:'one-time-bind',expires_seconds:600,server_url:fake.location.origin};
const managedPayload=pin=>JSON.stringify({
 'android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM':'base64-checksum',
 'android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION':'https://updates.example/BlazeRental.apk',
 'android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE':{
   server_url:fake.location.origin,enrollment_token:'one-time-managed',
   device_name:'Fixture',server_cert_sha256:pin
 }
});
const managed=pin=>({ok:true,qr_type:'device_owner',qr_payload:managedPayload(pin),
 enrollment_token:'one-time-managed',expires_seconds:600,apk_version:'0.6-rc',apk_version_code:60000,
 apk_url:'https://updates.example/BlazeRental.apk'});

function assertQrRoundTrip(response){
 assert.match(get('qrBox').innerHTML,/<svg\b/,'the real renderer must produce SVG');
 const count=lastSymbol.getModuleCount(),scale=4,side=(count+8)*scale;
 const rgba=new Uint8ClampedArray(side*side*4).fill(255);
 for(let row=0;row<count;row++)for(let column=0;column<count;column++){
  if(!lastSymbol.isDark(row,column))continue;
  for(let y=0;y<scale;y++)for(let x=0;x<scale;x++){
   const offset=(((row+4)*scale+y)*side+(column+4)*scale+x)*4;
   rgba[offset]=rgba[offset+1]=rgba[offset+2]=0;
  }
 }
 const decoded=jsQR(rgba,side,side,{inversionAttempts:'dontInvert'});
 assert(decoded,'independent decoder could not read the actual QR modules');
 assert.deepEqual(Array.from(decoded.binaryData),Array.from(Buffer.from(response.qr_payload,'utf8')),
  'actual QR bytes must exactly match the server payload UTF-8 bytes');
 assert.equal(decoded.data,response.qr_payload,'scanned QR text differs from the server payload');
 assert.deepEqual(JSON.parse(decoded.data),JSON.parse(response.qr_payload),
  'scanned QR JSON differs from the server response');
}

function responseFor(mode,label){
 const response=mode==='binding'?{...unmanaged}:managed('a'.repeat(64));
 const payload=JSON.parse(response.qr_payload);
 const binding=payload['android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE']||payload;
 binding.device_name=label;
 response.qr_payload=JSON.stringify(payload);
 return response;
}

async function reply(mode,response,label){
 get('addRentalLabel').value=label;
 const pending=mode==='binding'?qr.generateBindingQr():qr.generateProvisioningQr();
 assert.deepEqual(requests.at(-1),{
  action:mode==='binding'?'rental_binding_qr':'rental_provisioning_qr',
  body:{label,server_url:fake.location.origin}
 },'QR encoding must not change the request action or body');
 resolveApi(response);
 await pending;
}

function assertQrDisplay(response){
 assert.equal(get('qrResult').classList.contains('hidden'),false);
 assert.equal(get('qrReveal').hidden,false);
 assert(!get('qrToken').textContent.includes(response.enrollment_token),'secret shown without reveal');
 const managed=response.qr_type==='device_owner';
 assert.match(get('qrNotice').textContent,managed?/MANAGED SETUP/:/STANDARD BINDING/);
 assert.equal(get('qrMeta').textContent,managed?
  'APK '+response.apk_version+' ('+response.apk_version_code+') \u00b7 '+response.apk_url+'\nServer TLS pin: included':
  'Server '+response.server_url+'\nServer TLS pin: NOT INCLUDED \u00b7 lower security');
}

const failures=[];
async function check(name,run){
 try{await run();console.log('PASS: '+name)}catch(error){
  failures.push(name);console.error('FAIL: '+name+': '+String(error.message).split('\n')[0]);
 }
}
(async()=>{
 // An HTTP reply from a CLOSED modal must never resurrect its QR.
 qr.openAdd();
 const stale=qr.generateBindingQr();
 assert.equal(calls,1);
 qr.closeAdd();
 resolveApi(unmanaged);
 await stale;
 assert.equal(rendererCount,0,'stale QR must not render');
 assert.equal(get('qrResult').classList.contains('hidden'),true);
 // Reject server claiming "managed" mode but omitting local TLS pin.
 qr.openAdd();
 let pending=qr.generateProvisioningQr();
 resolveApi(managed(''));
 await pending;
 assert.equal(rendererCount,0,'unpinned Device Owner QR rendered');
 assert(alerts.some(x=>/missing certificate pin/i.test(x.msg)));
 assert.equal(get('qrResult').classList.contains('hidden'),true);
 // Valid managed QR displays encoded QR but NEVER puts secret in text until
 // operator explicitly clicks Reveal. This is display hygiene, not vaulting.
 const validPin='a'.repeat(64);
 pending=qr.generateProvisioningQr();
 resolveApi(managed(validPin));
 await pending;
 assert.equal(rendererCount,1);
 assert(!get('qrToken').textContent.includes('one-time-managed'),'secret shown without consent');
 assert.equal(get('qrReveal').hidden,false);
 assert(get('qrMeta').textContent.includes('included'));
 get('qrReveal').onclick();
 assert(get('qrToken').textContent.includes('one-time-managed'),'reveal action does not work');
 qr.closeAdd();
 assert.equal(get('qrToken').textContent,'','secret remained visible after close');
 // Error on wrong QR route: no accidental privilege confusion.
 qr.openAdd();
 pending=qr.generateProvisioningQr();
 resolveApi(unmanaged);
 await pending;
 assert.equal(rendererCount,1);
 assert(alerts.some(x=>/mode mismatch/i.test(x.msg)));
 console.log('PASS: rental QR browser model rejects stale responses, unpinned managed setup, reveals token only on request and distinguishes setup modes');

 const originalConverter=encoder.stringToBytes;
 const originalUtf8=encoder.stringToBytesFuncs['UTF-8'];
 // A distinct prior converter proves that rendering restores its caller's
 // exact converter reference, rather than assuming the vendor default.
 const priorConverter=value=>encoder.stringToBytesFuncs.default(value);
 const labels=['Rental phone','Caf\u00e9','\u7f51','\ud83d\ude00','Caf\u00e9 \u7f51\u7edc \ud83d\ude00'];
 for(const mode of ['binding','device_owner']){
  for(const label of labels){
   await check(`${mode}: actual QR preserves ${JSON.stringify(label)} and restores the prior converter`,async()=>{
    encoder.stringToBytes=priorConverter;
    try{
     qr.openAdd();
     const response=responseFor(mode,label),snapshot=JSON.stringify(response);
     await reply(mode,response,label);
     assert.equal(encoder.stringToBytes,priorConverter,'successful rendering did not restore the prior converter');
     assertQrDisplay(response);
     assertQrRoundTrip(response);
     assert.equal(JSON.stringify(response),snapshot,'rendering must not mutate API response metadata');
    }finally{
     encoder.stringToBytes=originalConverter;
     qr.closeAdd();
    }
   });
  }

  for(const stage of ['factory','addData','make','createSvgTag','encoder','missingUTF8']){
   await check(`${mode}: ${stage} failure restores the prior converter and clears stale QR/token output`,async()=>{
    encoder.stringToBytes=priorConverter;
    try{
     qr.openAdd();
     const label='Failure recovery fixture',response=responseFor(mode,label),snapshot=JSON.stringify(response);
     await reply(mode,response,label);
     assert.equal(encoder.stringToBytes,priorConverter,'seed QR did not restore the prior converter');
     assertQrDisplay(response);
     get('qrReveal').onclick();
     assert(get('qrToken').textContent.includes(response.enrollment_token),'seed token must be visible before the failed retry');
     const oldReveal=get('qrReveal').onclick,completed=rendererCount;
     failureStage=stage;
     if(stage==='encoder')encoder.stringToBytesFuncs['UTF-8']=()=>{throw new Error('injected UTF-8 encoder failure');};
     if(stage==='missingUTF8')encoder.stringToBytesFuncs['UTF-8']=undefined;
     await reply(mode,response,label);
     assert.equal(encoder.stringToBytes,priorConverter,'failed rendering did not restore the prior converter');
     assert.equal(get('qrBox').innerHTML,'','failed retry retained a scannable previous QR');
     assert.equal(get('qrToken').textContent,'','failed retry retained a revealed token');
     assert.equal(get('qrMeta').textContent,'','failed retry retained success metadata');
     assert.equal(get('qrNotice').textContent,'','failed retry retained a success notice');
     assert.equal(get('qrReveal').hidden,true,'failed retry retained a token reveal control');
     assert.equal(get('qrResult').classList.contains('hidden'),true,'failed retry still displays a QR result');
     assert.equal(rendererCount,completed,'failed renderer completed a replacement SVG');
     assert.equal(alerts.at(-1).bad,true);
     assert.match(alerts.at(-1).msg,/renderer failed/i);
     oldReveal();
     assert.equal(get('qrToken').textContent,'','old reveal callback resurrected a cleared token');
     assert.equal(JSON.stringify(response),snapshot,'renderer failure must not mutate API response metadata');

     failureStage='';
     encoder.stringToBytesFuncs['UTF-8']=originalUtf8;
     await reply(mode,response,label);
     assert.equal(encoder.stringToBytes,priorConverter,'corrected retry did not restore the prior converter');
     assertQrDisplay(response);
     assert.match(get('qrBox').innerHTML,/<svg\b/,'corrected retry must generate a real QR');
    }finally{
     failureStage='';
     encoder.stringToBytesFuncs['UTF-8']=originalUtf8;
     encoder.stringToBytes=originalConverter;
     qr.closeAdd();
    }
   });
  }
 }
 assert.equal(failures.length,0,`${failures.length} real-renderer checks failed: ${failures.join('; ')}`);
 console.log('PASS: real admin QR round trips preserve ASCII and Unicode in both modes; renderer failures clear output and restore the prior converter');
})().catch(error=>{console.error(error.stack||error);process.exitCode=1});
