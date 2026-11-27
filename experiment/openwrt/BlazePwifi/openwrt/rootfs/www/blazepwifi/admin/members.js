(function(){
'use strict';
const q=s=>document.querySelector(s), C=()=>window.BlazeCore;
let importPreviewToken='';
function mins(sec){sec=Math.max(0,+sec||0);const h=Math.floor(sec/3600),m=Math.floor((sec%3600)/60);return h?h+'h '+m+'m':m+'m'}
function esc(v){return C().esc(v)}
function card(x){
  const user=esc(x.username||'');
  return '<div class="card member-card" data-member="'+user+'"><div class="card-body">'+
    '<div class="device-top"><div><div class="device-name">'+user+'</div><div class="device-meta">'+esc(x.label||'No label')+'</div></div>'+
    '<div class="toolbar"><span class="badge '+((+x.enabled)?'good':'bad')+'">'+((+x.enabled)?'ENABLED':'DISABLED')+'</span><span class="badge">rev '+esc(x.revision||0)+'</span></div></div>'+
    '<div class="switch-row"><span><b>Banked time</b><div class="small muted">Authoritative BlazePwifi balance</div></span><span class="badge good">'+mins(x.banked_seconds)+'</span></div>'+
    '<label><span class="field-label">Label / display name</span><input class="field label" value="'+esc(x.label||'')+'"></label>'+
    '<div class="switch-row"><span>Member enabled</span><input class="toggle enabled" type="checkbox" '+((+x.enabled)?'checked':'')+'></div>'+
    '<div class="toolbar" style="margin-top:12px"><button class="btn primary sm" onclick="BlazeMembers.save(\''+user+'\')">Save member</button><button class="btn sm" onclick="BlazeMembers.loadEvents(\''+user+'\')">Events</button></div>'+
    '<div class="form-grid" style="margin-top:14px"><label><span class="field-label">Minutes</span><input class="field minutes" type="number" min="0" max="525600" value="30"></label>'+
    '<label><span class="field-label">Balance action</span><select class="field balanceMode"><option value="add">Add</option><option value="subtract">Subtract</option><option value="set">Set exact</option></select></label></div>'+
    '<button class="btn sm" style="margin-top:10px" onclick="BlazeMembers.balance(\''+user+'\')">Apply banked time</button>'+
    '<div class="form-grid" style="margin-top:14px"><label class="span2"><span class="field-label">New member password</span><input class="field password" type="password" autocomplete="new-password" placeholder="Admin reset only"></label></div>'+
    '<div class="toolbar" style="margin-top:10px"><button class="btn sm" onclick="BlazeMembers.password(\''+user+'\')">Reset password</button><button class="btn danger sm" onclick="BlazeMembers.remove(\''+user+'\')">Delete member</button></div>'+
    '<div class="small muted" style="margin-top:10px">Updated '+(x.updated?new Date((+x.updated)*1000).toLocaleString():'—')+' · '+esc(x.source||'unknown')+'</div>'+
    '</div></div>';
}
function node(user){return document.querySelector('[data-member="'+CSS.escape(user)+'"]')}
function decodeBase64Utf8(b64){
  const bin=atob(b64||''),bytes=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
  return new TextDecoder('utf-8',{fatal:true}).decode(bytes);
}
function encodeBytesBase64(bytes){
  // Chunk size must be divisible by 3 so concatenated Base64 chunks have no mid-stream padding.
  let out='',chunk=0x6000;
  for(let i=0;i<bytes.length;i+=chunk){
    const part=bytes.subarray(i,Math.min(bytes.length,i+chunk));
    let s='';for(let j=0;j<part.length;j++)s+=String.fromCharCode(part[j]);
    out+=btoa(s);
  }
  return out;
}
async function exportMetadata(){
  const x=await C().api('member_export');
  if(!x.ok){C().toast(x.error||'Member export failed',true);return}
  try{
    const text=decodeBase64Utf8(x.payload_b64||'');
    const blob=new Blob([text],{type:'text/plain;charset=utf-8'});
    const a=document.createElement('a');
    a.href=URL.createObjectURL(blob);
    a.download=x.filename||'BlazePwifi-members.blazemembers';
    document.body.appendChild(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(a.href),1000);
    C().toast('Member metadata exported without password verifier material.');
  }catch(e){C().toast('Export payload could not be decoded',true)}
}
function clearImportPreview(message){
  importPreviewToken='';
  const btn=q('#memberImportApply');if(btn)btn.disabled=true;
  const out=q('#memberImportPreview');if(out)out.textContent=message||'No import preview loaded.';
}
async function previewImport(){
  const input=q('#memberImportFile'),summary=q('#memberImportSummary');
  const file=input&&input.files&&input.files[0];
  clearImportPreview('Reading metadata file…');
  if(!file){if(summary)summary.textContent='Choose a .blazemembers file first.';return}
  if(file.size>262144){if(summary)summary.textContent='Import file is larger than the 256 KiB limit.';return}
  let bytes;
  try{bytes=new Uint8Array(await file.arrayBuffer())}catch(e){if(summary)summary.textContent='Unable to read the selected file.';return}
  const x=await C().api('member_import_preview',{payload_b64:encodeBytesBase64(bytes)});
  if(!x.ok){if(summary)summary.textContent=x.error||'Import preview failed';clearImportPreview(x.error||'Import preview failed');C().toast(x.error||'Import preview failed',true);return}
  importPreviewToken=x.preview_token||'';
  const items=x.items||[],lines=items.map(v=>{
    const status=String(v.status||'').toUpperCase();
    const enabled=(+v.requested_enabled)?'requested enabled':'disabled';
    return status+'  '+(v.username||'')+'  '+(v.label||'')+'  '+Math.floor((+v.banked_seconds||0)/60)+'m  '+enabled;
  });
  if(summary)summary.textContent='Preview: '+(x.count||0)+' records · '+(x.creates||0)+' new · '+(x.collisions||0)+' collisions · '+(x.requested_enabled||0)+' requested enabled. New members will still be created disabled until password reset.';
  const out=q('#memberImportPreview');if(out)out.textContent=lines.length?lines.join('\n'):'File contains no member records.';
  const btn=q('#memberImportApply');if(btn)btn.disabled=!importPreviewToken;
}
async function applyImport(){
  if(!importPreviewToken){C().toast('Preview the import file first.',true);return}
  const pass=q('#memberImportPassword'),password=(pass&&pass.value)||'',policy=(q('#memberImportPolicy')&&q('#memberImportPolicy').value)||'abort';
  if(!password){C().toast('Admin password is required to apply an import.',true);return}
  if(policy==='update'&&!confirm('Metadata-only update existing members? Existing password verifier material will be preserved, but label, enabled state and banked balance may change.'))return;
  if(policy!=='update'&&!confirm('Apply the reviewed member import with collision policy "'+policy+'"? New members will be created disabled and require password reset.'))return;
  const token=importPreviewToken;
  importPreviewToken='';
  const btn=q('#memberImportApply');if(btn)btn.disabled=true;
  const x=await C().api('member_import_apply',{preview_token:token,collision_policy:policy,password});
  if(pass)pass.value='';
  if(!x.ok){
    clearImportPreview(x.error||'Import apply failed. Preview the file again before retrying.');
    C().toast(x.error||'Import apply failed',true);
    return;
  }
  const summary=q('#memberImportSummary');
  if(summary)summary.textContent='Import applied: '+(x.created||0)+' created · '+(x.updated||0)+' updated · '+(x.skipped||0)+' skipped · central revision '+(x.revision||0)+'. New imported accounts require password reset before enabling.';
  clearImportPreview('Import applied successfully. Preview is single-use and has been cleared.');
  if(q('#memberImportFile'))q('#memberImportFile').value='';
  await load();await loadEvents('');
}
async function load(render=true){
  const x=await C().api('member_list');
  if(!x.ok){if(render)C().toast(x.error||'Member load failed',true);return}
  if(q('#memberRevision'))q('#memberRevision').textContent='Central revision '+(x.revision||0);
  const items=x.members||[];
  if(render)q('#memberCards').innerHTML=items.length?items.map(card).join(''):'<div class="card empty">No Pisonet members yet.</div>';
}
async function create(){
  const username=q('#memberCreateUser').value.trim(),label=q('#memberCreateLabel').value.trim(),password=q('#memberCreatePassword').value;
  if(!username||password.length<8){C().toast('Username and a password of at least 8 characters are required',true);return}
  const x=await C().api('member_create',{username,label,password});
  q('#memberCreatePassword').value='';
  C().toast(x.ok?'Member created':(x.error||'Member creation failed'),!x.ok);
  if(x.ok){q('#memberCreateUser').value='';q('#memberCreateLabel').value='';await load();await loadEvents('')}
}
async function save(user){
  const n=node(user);if(!n)return;
  const x=await C().api('member_update',{username:user,label:n.querySelector('.label').value.trim(),enabled:n.querySelector('.enabled').checked?'1':'0'});
  C().toast(x.ok?'Member updated':(x.error||'Member update failed'),!x.ok);if(x.ok)load();
}
async function balance(user){
  const n=node(user);if(!n)return;
  const minutes=Math.max(0,parseInt(n.querySelector('.minutes').value||'0',10)||0);
  const x=await C().api('member_balance',{username:user,mode:n.querySelector('.balanceMode').value,seconds:String(minutes*60)});
  C().toast(x.ok?'Banked time updated':(x.error||'Balance update failed'),!x.ok);if(x.ok){await load();await loadEvents(user)}
}
async function password(user){
  const n=node(user);if(!n)return;const password=n.querySelector('.password').value;
  if(password.length<8){C().toast('Use at least 8 characters for the member password',true);return}
  const x=await C().api('member_password',{username:user,password});n.querySelector('.password').value='';
  C().toast(x.ok?'Member password reset':(x.error||'Password reset failed'),!x.ok);if(x.ok)loadEvents(user);
}
async function remove(user){
  if(!confirm('Delete Pisonet member '+user+'? Banked time and the account will be removed.'))return;
  const x=await C().api('member_delete',{username:user});
  C().toast(x.ok?'Member deleted':(x.error||'Delete failed'),!x.ok);if(x.ok){await load();await loadEvents('')}
}
async function transfer(){
  const from=q('#memberTransferFrom').value.trim(),to=q('#memberTransferTo').value.trim(),minutes=Math.max(1,parseInt(q('#memberTransferMinutes').value||'0',10)||0);
  const x=await C().api('member_transfer',{from_username:from,to_username:to,seconds:String(minutes*60)});
  C().toast(x.ok?'Member time transferred':(x.error||'Transfer failed'),!x.ok);if(x.ok){await load();await loadEvents(from)}
}
async function loadEvents(user){
  const x=await C().api('member_events',{username:user||'',limit:'64'});
  if(!x.ok){C().toast(x.error||'Member events failed',true);return}
  const e=x.events||[];
  q('#memberEvents').textContent=e.length?e.slice().reverse().map(v=>{
    const dt=v.timestamp?new Date((+v.timestamp)*1000).toLocaleString():'—';
    const delta=(+v.delta_seconds||0);return dt+'  '+(v.username||'')+'  '+(v.kind||'')+'  '+(delta>=0?'+':'')+delta+'s  '+(v.source||'');
  }).join('\n'):'No member events yet.';
}
window.BlazeMembers={load,create,save,balance,password,remove,transfer,loadEvents,exportMetadata,previewImport,applyImport};
})();