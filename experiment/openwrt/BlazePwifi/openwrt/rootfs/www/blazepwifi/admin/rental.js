(function(){
'use strict';
const q=s=>document.querySelector(s), C=()=>window.BlazeCore;let devices=[],qrGeneration=0;
function paid(d){return (+d.lease_until||0)>Math.floor(Date.now()/1000)}
const QUICK=[['volume_down','Volume −'],['volume_up','Volume +'],['floating_timer','Floating timer'],['network_status','Network status'],['battery_status','Battery status'],['bluetooth_status','Bluetooth'],['flashlight','Flashlight']];
function appList(d){const inv=String(d.inventory||'').split(',').map(x=>x.trim()).filter(Boolean),allowed=new Set(String(d.allowed_packages||'').split(',').map(x=>x.trim()).filter(Boolean)),hidden=new Set(String(d.hidden_packages||'').split(',').map(x=>x.trim()).filter(Boolean)),all=d.allowed_packages==='*';if(!inv.length)return '<div class="muted small">No app inventory reported yet. The phone will report installed launcher apps on its next sync.</div>';return inv.map(pkg=>'<div class="app-check"><span><b>'+C().esc(pkg.split('.').pop())+'</b><span>'+C().esc(pkg)+'</span></span><label class="small">Allow <input class="allowApp" type="checkbox" data-pkg="'+C().esc(pkg)+'" '+((all||allowed.has(pkg))&&!hidden.has(pkg)?'checked':'')+' onchange="if(this.checked)this.closest(\'.app-check\').querySelector(\'.hideApp\').checked=false"></label><label class="small">Hide <input class="hideApp" type="checkbox" data-pkg="'+C().esc(pkg)+'" '+(hidden.has(pkg)?'checked':'')+' onchange="if(this.checked)this.closest(\'.app-check\').querySelector(\'.allowApp\').checked=false"></label></div>').join('')}
function quickList(d){const enabled=new Set(String(d.quick_controls||'').split(',').map(x=>x.trim()).filter(Boolean));return QUICK.map(x=>'<label class="app-check"><input class="quickControl" type="checkbox" data-control="'+x[0]+'" '+(enabled.has(x[0])?'checked':'')+'><span><b>'+x[1]+'</b></span></label>').join('')}
function card(d){const id=C().esc(d.device_id),isPaid=paid(d),mode=d.launcher_mode||'rental',rev=+d.policy_revision||0,timerMode=d.timer_mode||'overlay';return '<div class="card device-card" data-device="'+id+'"><div class="device-top"><div><div class="device-name">'+C().esc(d.label||'Rental phone')+'</div><div class="device-meta mono">'+id+'</div></div><div class="toolbar"><span class="badge '+(isPaid?'good':'bad')+'">'+(isPaid?'PAID':'LOCKED')+'</span><span class="badge">'+C().esc(mode)+'</span></div></div><div class="form-grid" style="margin-top:14px"><label><span class="field-label">Preferred controller</span><input class="field vendo" value="'+C().esc(d.preferred_vendo||'')+'" placeholder="Auto"></label><label><span class="field-label">Policy revision</span><input class="field rev" value="'+rev+'" readonly></label><label><span class="field-label">Floating timer policy</span><select class="field timerMode"><option value="overlay" '+(timerMode==='overlay'?'selected':'')+'>Customer may use overlay</option><option value="always" '+(timerMode==='always'?'selected':'')+'>Always on while paid</option><option value="off" '+(timerMode==='off'?'selected':'')+'>Disabled</option></select></label><label><span class="field-label">Advanced hidden package IDs</span><input class="field hiddenPkgs" value="'+C().esc(d.hidden_packages||'')+'" placeholder="optional comma-separated fallback"></label><div class="span2"><span class="field-label">Installed apps — Allow / Hide</span><div class="apps">'+appList(d)+'</div></div><div class="span2"><span class="field-label">Quick controls shown to customer</span><div class="apps quick-controls">'+quickList(d)+'</div></div></div><div class="switch-row"><span><b>Use device as is</b><div class="small muted">Disable rental restrictions on this phone</div></span><input class="toggle unrestricted" type="checkbox" '+(mode==='unrestricted'?'checked':'')+'></div><div class="switch-row"><span>Customer may toggle floating timer</span><input class="toggle timerToggle" type="checkbox" '+((+d.timer_user_toggle)!==0?'checked':'')+'></div><div class="switch-row"><span>Mirror notifications</span><input class="toggle notifications" type="checkbox" '+((+d.notifications_enabled)!==0?'checked':'')+'></div><div class="device-actions"><button class="btn primary sm" onclick="BlazeRental.savePolicy(\''+id+'\')">Save policy</button><button class="btn sm" onclick="BlazeRental.addTime(\''+id+'\',3600)">+ 1 hour</button><button class="btn sm" onclick="BlazeRental.expire(\''+id+'\')">Expire now</button><button class="btn sm" onclick="BlazeRental.rename(\''+id+'\')">Rename</button><button class="btn sm" onclick="BlazeRental.setAdminPassword(\''+id+'\')">'+(d.admin_password_set?'Change device admin password':'Set device admin password')+'</button><button class="btn danger sm" onclick="BlazeRental.revoke(\''+id+'\')">Revoke</button></div><div class="small muted" style="margin-top:10px">Last seen: '+(d.last_seen?new Date(d.last_seen*1000).toLocaleString():'never')+' • '+(d.admin_password_set?'Admin password set':'Admin password not set')+'</div></div>'}
async function loadUpdateChannel(){
  const x=await C().api('rental_update_get');
  if(!x.ok){C().toast(x.error||'Unable to load Rental update channel',true);return}
  const u=x.update||{};
  const set=(id,v)=>{const n=q(id);if(n)n.value=v==null?'':v};
  set('#rentalUpdateVersion',u.version||''); set('#rentalUpdateCode',u.version_code||'');
  set('#rentalUpdateUrl',u.apk_url||''); set('#rentalUpdateSha',u.apk_sha256||'');
  set('#rentalRollbackVersion',u.rollback_version||''); set('#rentalRollbackCode',u.rollback_version_code||'');
  set('#rentalRollbackUrl',u.rollback_url||''); set('#rentalRollbackSha',u.rollback_sha256||'');
  const s=q('#rentalUpdateState'); if(s)s.textContent=u.available?('Published '+u.version+' ('+u.version_code+') • rollback '+(u.rollback_version||'none')):'No Rental update currently published.';
}
async function saveUpdateChannel(){
  const data={
    version:q('#rentalUpdateVersion').value.trim(),version_code:q('#rentalUpdateCode').value,
    apk_url:q('#rentalUpdateUrl').value.trim(),apk_sha256:q('#rentalUpdateSha').value.trim(),
    rollback_version:q('#rentalRollbackVersion').value.trim(),rollback_version_code:q('#rentalRollbackCode').value,
    rollback_url:q('#rentalRollbackUrl').value.trim(),rollback_sha256:q('#rentalRollbackSha').value.trim()
  };
  if(!/^https:\/\//i.test(data.apk_url)||!/^[0-9a-f]{64}$/i.test(data.apk_sha256)){C().toast('Valid HTTPS APK URL and SHA-256 are required',true);return}
  if(data.rollback_url&&(!/^https:\/\//i.test(data.rollback_url)||!/^[0-9a-f]{64}$/i.test(data.rollback_sha256))){C().toast('Rollback rescue URL/SHA is invalid',true);return}
  const x=await C().api('rental_update_set',data);
  C().toast(x.ok?'Rental update channel published':(x.error||'Publish failed'),!x.ok);
  if(x.ok)loadUpdateChannel();
}
async function load(render=true){const x=await C().api('rental_device_list');if(!x.ok){if(render)C().toast(x.error||'Unable to load rentals',true);return}devices=x.devices||[];const now=Math.floor(Date.now()/1000),paidCount=devices.filter(d=>(+d.lease_until||0)>now).length;q('#metricRentals').textContent=devices.length;q('#metricPaidRentals').textContent=paidCount+' paid • '+(devices.length-paidCount)+' locked';if(render){q('#rentalCards').innerHTML=devices.length?devices.map(card).join(''):'<div class="card empty">No rental devices enrolled yet.</div>'}const cfg=await C().api('config_get',{key:'rental_seconds_per_pulse'});if(cfg.ok)q('#pulseSeconds').value=cfg.value||600;if(render)loadUpdateChannel()}
async function savePulse(){const x=await C().api('config_set',{key:'rental_seconds_per_pulse',value:q('#pulseSeconds').value});C().toast(x.ok?'Coin rate saved':(x.error||'Save failed'),!x.ok)}
let qrSecret='';
function clearQr(){
  qrSecret='';
  q('#qrBox').innerHTML='';
  q('#qrNotice').textContent='';
  q('#qrMeta').textContent='';
  q('#qrToken').textContent='';
  q('#qrReveal').hidden=true;
  q('#qrResult').classList.add('hidden');
}
function openAdd(){
  qrGeneration++;
  q('#addRentalServer').value=location.origin;
  clearQr();
  q('#addRentalModal').classList.remove('hidden');
}
function closeAdd(){
  // Pending HTTP enrollment replies must NEVER resurrect closed/old QR codes.
  qrGeneration++;
  clearQr();
  q('#addRentalModal').classList.add('hidden');
}
function renderQrResult(x){
  if(!x||typeof x.qr_payload!=='string'||!x.enrollment_token||
     !['binding','device_owner'].includes(x.qr_type)){
    C().toast('Invalid enrollment response. No QR displayed.',true);return false;
  }
  let data;
  try{data=JSON.parse(x.qr_payload)}catch(_){
    C().toast('Malformed enrollment payload. No QR displayed.',true);return false;
  }
  const managed=x.qr_type==='device_owner';
  const cfg=managed?data['android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE']:data;
  const pin=cfg&&cfg.server_cert_sha256;
  const hasPin=typeof pin==='string'&&/^[a-f0-9]{64}$/i.test(pin);
  if(managed&&(!hasPin||!data['android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM']||
      !data['android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION'])){
    C().toast('Managed QR is missing certificate pin or verified APK download metadata.',true);
    return false;
  }
  // Do not show a secret QR until the renderer has successfully completed.
  let svg;
  try{
    const previousEncoder=qrcode.stringToBytes,utf8Encoder=qrcode.stringToBytesFuncs['UTF-8'];
    if(typeof utf8Encoder!=='function')throw new Error('UTF-8 QR encoder is unavailable');
    // Keep the encoding change local to this synchronous rental render.
    try{
      qrcode.stringToBytes=utf8Encoder;
      const qr=qrcode(0,'M');qr.addData(x.qr_payload);qr.make();
      svg=qr.createSvgTag({cellSize:5,margin:3,scalable:true});
    }finally{
      qrcode.stringToBytes=previousEncoder;
    }
  }catch(e){
    C().toast('QR renderer failed: '+(e&&e.message?e.message:'unknown renderer error'),true);
    return false;
  }
  q('#qrBox').innerHTML=svg;
  q('#qrNotice').textContent=managed?
    'MANAGED SETUP · Scan during factory-reset Android Setup Wizard. Use a signed APK whose checksum and permanent signer you have verified.':
    'STANDARD BINDING · Scan inside an installed BlazeRental app. Does not grant Device Owner protections.';
  q('#qrMeta').textContent=(managed?
    'APK '+(x.apk_version||'')+' ('+(x.apk_version_code||0)+') · '+(x.apk_url||''):
    'Server '+(x.server_url||''))+'\nServer TLS pin: '+(hasPin?'included':'NOT INCLUDED · lower security');
  qrSecret=String(x.enrollment_token);
  q('#qrToken').textContent='One-time token hidden · expires in '+(Number(x.expires_seconds)||600)+' seconds';
  const reveal=q('#qrReveal');
  reveal.hidden=false;
  reveal.onclick=function(){
    if(!qrSecret||!confirm('Display the temporary enrollment token? Only reveal it to a trusted installer.'))return;
    const current=qrSecret;
    q('#qrToken').textContent='One-time token: '+current;
    const stamp=qrGeneration;
    setTimeout(function(){
      if(stamp===qrGeneration&&qrSecret===current)
        q('#qrToken').textContent='One-time token hidden · scan the QR instead';
    },15000);
  };
  q('#qrResult').classList.remove('hidden');
  const stamp=++qrGeneration;
  setTimeout(function(){
    if(qrGeneration!==stamp)return;
    clearQr();
    q('#qrResult').classList.remove('hidden');
    q('#qrNotice').textContent='Enrollment QR expired. Generate a new QR before scanning.';
  },Math.max(1,Math.min(3600,Number(x.expires_seconds)||600))*1000);
  return true;
}
async function generateQr(action){
  const request=++qrGeneration;
  clearQr();
  const label=q('#addRentalLabel').value||'Rental phone';
  const server=q('#addRentalServer').value||location.origin;
  const managed=action==='rental_provisioning_qr';
  if(managed&&!/^https:\/\//i.test(server)){
    C().toast('Device Owner provisioning requires an HTTPS server.',true);return;
  }
  q('#qrResult').classList.remove('hidden');
  q('#qrNotice').textContent='Generating one-time '+(managed?'managed provisioning':'binding')+' QR…';
  const x=await C().api(action,{label,server_url:server});
  if(request!==qrGeneration||q('#addRentalModal').classList.contains('hidden'))return;
  if(!x.ok){
    clearQr();
    C().toast(x.error||'Enrollment QR generation failed',true);
    return;
  }
  if(x.qr_type!==(managed?'device_owner':'binding')){
    clearQr();
    C().toast('Enrollment QR mode mismatch. No token displayed.',true);
    return;
  }
  if(!renderQrResult(x))clearQr();
}
async function generateBindingQr(){return generateQr('rental_binding_qr')}
async function generateProvisioningQr(){return generateQr('rental_provisioning_qr')}
function node(id){return document.querySelector('[data-device="'+CSS.escape(id)+'"]')}
async function savePolicy(id){const n=node(id);if(!n)return;const allowed=Array.from(n.querySelectorAll('.allowApp:checked')).map(x=>x.dataset.pkg).join(',');const hiddenSet=new Set(String(n.querySelector('.hiddenPkgs').value||'').split(',').map(x=>x.trim()).filter(Boolean));Array.from(n.querySelectorAll('.hideApp:checked')).forEach(x=>hiddenSet.add(x.dataset.pkg));const hidden=Array.from(hiddenSet).join(',');const quick=Array.from(n.querySelectorAll('.quickControl:checked')).map(x=>x.dataset.control).join(',');const data={device_id:id,expected_revision:n.querySelector('.rev').value,launcher_mode:n.querySelector('.unrestricted').checked?'unrestricted':'rental',allowed_packages:allowed||'-',hidden_packages:hidden||'-',preferred_vendo:n.querySelector('.vendo').value,timer_mode:n.querySelector('.timerMode').value,timer_user_toggle:n.querySelector('.timerToggle').checked?'1':'0',notifications_enabled:n.querySelector('.notifications').checked?'1':'0',quick_controls:quick||'-'};const x=await C().api('rental_policy_set',data);if(!x.ok){C().toast(x.error||'Policy update failed',true);if(x.current_revision!=null)load();return}C().toast('Policy saved • revision '+x.policy_revision);load()}
async function addTime(id,seconds){const x=await C().api('rental_lease_add',{device_id:id,seconds});C().toast(x.ok?'Rental time added':(x.error||'Time update failed'),!x.ok);load()}
async function expire(id){if(!confirm('Expire this rental session now?'))return;const x=await C().api('rental_lease_expire',{device_id:id});C().toast(x.ok?'Rental expired':(x.error||'Expire failed'),!x.ok);load()}
async function rename(id){const d=devices.find(x=>x.device_id===id),name=prompt('Rental phone label',d?d.label:'Rental phone');if(!name)return;const x=await C().api('rental_device_rename',{device_id:id,label:name});C().toast(x.ok?'Renamed':(x.error||'Rename failed'),!x.ok);load()}
async function setAdminPassword(id){const pass=prompt('Device administrator password (8+ characters)');if(pass===null)return;if(pass.length<8){C().toast('Use at least 8 characters',true);return}const x=await C().api('rental_admin_password_set',{device_id:id,admin_password:pass});C().toast(x.ok?'Device admin password updated':(x.error||'Password update failed'),!x.ok);if(x.ok)load()}
async function revoke(id){if(!confirm('Revoke this phone? It must be enrolled again before it can rent.'))return;const x=await C().api('rental_device_revoke',{device_id:id});C().toast(x.ok?'Device revoked':(x.error||'Revoke failed'),!x.ok);load()}
window.BlazeRental={load,loadUpdateChannel,saveUpdateChannel,savePulse,openAdd,closeAdd,generateBindingQr,generateProvisioningQr,savePolicy,addTime,expire,rename,setAdminPassword,revoke};
})();
