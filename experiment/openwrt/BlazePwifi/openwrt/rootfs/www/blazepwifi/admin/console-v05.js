(function(){
'use strict';
const q=s=>document.querySelector(s), C=()=>window.BlazeCore;
let terminalToken='',remoteLoadGeneration=0,remoteFormEditGeneration=0;
// Remote profile refreshes are asynchronous. Never let an older GET overwrite
// operator edits made while it was in flight (before the Save button is pressed).
const remoteFormSelectors='#remoteMode,#remoteNodeName,#remoteSiteLabel,#remoteAllowlist,#remoteHeartbeat,#remoteOffline,#remoteMonitoring,#remoteManagement,#remoteTerminal,#wgEndpoint,#wgPort,#wgAddress,#wgKeepalive,#wgPeerKey,#wgAllowedIps,#wgDns,#wgMtu,#ztNetworkId';
function recordRemoteFormEdit(event){
  const el=event.target;
  if(el&&el.matches&&el.matches(remoteFormSelectors))remoteFormEditGeneration++;
}
document.addEventListener('input',recordRemoteFormEdit,true);
document.addEventListener('change',recordRemoteFormEdit,true);
function fmtTemp(v){const n=+v||0;return n?((n>1000?n/1000:n).toFixed(1)+' °C'):'Not reported'}
async function loadSystem(){
  const x=await C().api('system_info');
  if(!x.ok){C().toast(x.error||'Hardware detection failed',true);return}
  const text=[
    x.model||'Unknown device',
    x.cpu||'Unknown CPU',
    x.kernel||'Unknown kernel',
    'Rootfs '+(x.rootfs||'Unknown'),
    'Temperature '+fmtTemp(x.temperature_milli_c),
    'Wi-Fi '+(x.wifi?'detected':'not detected'),
    'USB '+(x.usb?'detected':'not detected')
  ].join(' • ');
  const s=q('#systemSummary'); if(s)s.textContent=text;
  const d=q('#systemDetails'); if(d)d.textContent=text;
  const w=q('#wispBadge'); if(w){w.textContent=x.wifi?'Available':'No Wi-Fi radio detected';w.className='badge '+(x.wifi?'good':'');}
  const wc=q('#wanCapability'); if(wc)wc.textContent=(x.wifi?'Ethernet/WISP capability detected. ':'No Wi-Fi WISP capability currently detected. ')+(x.usb?'USB devices present.':'No USB device currently detected.');
}
async function loadStorage(){
  const o=q('#storageOutput'); if(o)o.textContent='Loading mounts…';
  const x=await C().api('storage_list');
  if(!o)return;
  if(!x.ok){o.textContent=x.error||'Unable to read storage';return}
  o.textContent=String(x.mounts||'No mounts reported').split(';').filter(Boolean).map(v=>{
    const p=v.split('|'); return (p[3]||'?')+'  device '+(p[0]||'?')+'  used '+(p[2]||'?')+'/'+(p[1]||'?')+' KB';
  }).join('\n');
}
function setRemoteEditable(enabled){
  ['#remoteMode','#remoteNodeName','#remoteSiteLabel','#remoteAllowlist','#remoteHeartbeat','#remoteOffline',
   '#remoteMonitoring','#remoteManagement','#remoteTerminal','#wgEndpoint','#wgPort','#wgAddress',
   '#wgKeepalive','#wgPeerKey','#wgAllowedIps','#wgDns','#wgMtu','#ztNetworkId','#remotePassword',
   '#wgKeyButton','#wgApplyButton','#wgDisableButton','#ztIdentityButton','#ztApplyButton','#ztDisableButton']
    .forEach(id=>{const n=q(id);if(n)n.disabled=!enabled});
}
function renderRemoteStatus(r){
  r=r||{};
  const rt=r.runtime||{},wg=q('#wgState'),zt=q('#ztState');
  if(wg){wg.textContent=r.wireguard||'Unavailable';wg.className='metric-value small '+(String(r.wireguard).indexOf('online:')===0?'good':'');}
  if(zt){zt.textContent=r.zerotier||'Unavailable';zt.className='metric-value small '+(String(r.zerotier).indexOf('ONLINE')>=0?'good':'');}
  const mode=q('#remoteModeState');if(mode)mode.textContent=r.mode||'disabled';
  const activation=String(rt.activation_state||'staged');
  const ready=q('#remoteReadyState');
  if(ready){
    if(r.mode==='disabled')ready.textContent='Remote access off';
    else if(activation==='active')ready.textContent='Live '+(rt.transport==='zerotier'?'ZeroTier':'WireGuard')+' active';
    else if(activation==='active_staged_changes')ready.textContent='Live '+(rt.transport==='zerotier'?'ZeroTier':'WireGuard')+' · staged changes not applied';
    else ready.textContent=r.ready?'Profile complete · '+activation:'Profile incomplete';
  }
  const node=q('#remoteNodeState');if(node)node.textContent=r.node_name||'BlazePwifi';
  const site=q('#remoteSiteState');if(site)site.textContent=r.site_label||'No site label';
  const act=q('#wgActivationState');if(act){act.textContent=activation;act.className='metric-value small '+(activation==='active'?'good':'');}
  const hs=q('#wgHandshakeState'),ztr=rt.zerotier||{};
  if(hs){
    const stamp=Number(rt.last_handshake||0);
    if(rt.transport==='zerotier'&&String(ztr.active)==='1')
      hs.textContent='ZeroTier '+(ztr.status||'—')+' · '+(ztr.interface||'no interface')+' · '+(ztr.address||'no IPv4');
    else
      hs.textContent=stamp>0?'Handshake '+new Date(stamp*1000).toLocaleString():(rt.last_error?'Last error: '+rt.last_error:(rt.apply_supported?'No verified handshake yet':'Live apply unavailable'));
  }
  const pub=q('#wgLocalPublicKey');if(pub)pub.value=rt.public_key||'';
  const ztn=q('#ztNodeId');if(ztn)ztn.value=ztr.node_id||'';
  const zts=q('#ztLiveState');
  if(zts){
    if(String(ztr.active)==='1')zts.textContent='Active · '+(ztr.status||'—')+' · '+(ztr.interface||'—')+' · '+(ztr.address||'—');
    else if(ztr.node_id)zts.textContent='Identity ready · node '+ztr.node_id+' · authorize this node before applying.';
    else zts.textContent=rt.apply_supported?'Identity not prepared yet.':'ZeroTier live apply unavailable on this target.';
  }
}
async function loadRemote(){
  const generation=++remoteLoadGeneration;
  const editAtStart=remoteFormEditGeneration;
  const x=await C().api('remote_status');
  if(generation!==remoteLoadGeneration)return;
  if(!x.ok){C().toast(x.error||'Remote status unavailable',true);return}
  renderRemoteStatus(x.remote||{});

  const cfg=await C().api('remote_config_get');
  if(generation!==remoteLoadGeneration)return;
  const state=q('#remoteConfigState');
  if(!cfg.ok){
    setRemoteEditable(false);
    if(state)state.textContent='Admin role required to view or edit the remote profile.';
    return;
  }
  setRemoteEditable(true);
  if(editAtStart!==remoteFormEditGeneration){
    // A previously scheduled status/config refresh completed after an edit.
    // Leave the unsaved fields alone; a save reads exactly what was entered.
    if(state)state.textContent='Remote status refreshed; unsaved profile edits were preserved.';
    return;
  }
  const v=cfg.config||{};
  const set=(id,val)=>{const n=q(id);if(n)n.value=val==null?'':val};
  set('#remoteMode',v.mode||'disabled');set('#remoteNodeName',v.node_name||'BlazePwifi');
  set('#remoteSiteLabel',v.site_label||'');set('#remoteAllowlist',v.source_allowlist||'');
  set('#remoteHeartbeat',v.heartbeat_seconds||30);set('#remoteOffline',v.offline_seconds||120);
  set('#wgEndpoint',v.wg_endpoint||'');set('#wgPort',v.wg_port||51820);set('#wgAddress',v.wg_address||'');
  set('#wgKeepalive',v.wg_keepalive==null?25:v.wg_keepalive);set('#wgPeerKey',v.wg_peer_public_key||'');
  set('#wgAllowedIps',v.wg_allowed_ips||'');set('#wgDns',v.wg_dns||'');set('#wgMtu',v.wg_mtu||1420);
  set('#ztNetworkId',v.zt_network_id||'');
  const check=(id,val)=>{const n=q(id);if(n)n.checked=String(val)==='1'||val===true};
  check('#remoteMonitoring',v.monitoring);check('#remoteManagement',v.management);check('#remoteTerminal',v.terminal);
  if(state){
    const rt=(x.remote&&x.remote.runtime)||{};
    if(v.mode==='wireguard'&&String(rt.activation_state||'staged')==='active_staged_changes')
      state.textContent='Profile saved. The existing WireGuard tunnel is still active with the previous applied profile; use Test & Apply to activate these staged changes.';
    else if(v.mode==='wireguard')
      state.textContent='WireGuard profile validated. Save and apply are separate operations; live activation requires a handshake and route-survival checks.';
    else if(v.mode==='zerotier'&&String(rt.activation_state||'staged')==='active_staged_changes')
      state.textContent='Profile saved. The existing ZeroTier tunnel remains active with the previously applied profile; use Test & Apply ZeroTier to activate staged changes.';
    else if(v.mode==='zerotier')
      state.textContent='ZeroTier profile validated. Prepare/authorize the node ID, then use Test & Apply ZeroTier.';
    else
      state.textContent='Remote access profile is disabled/staged.';
  }
}
async function saveRemote(){
  // Invalidate any in-flight page-load refresh before committing a new profile.
  ++remoteLoadGeneration;
  const pass=q('#remotePassword'),password=(pass&&pass.value)||'';
  if(!password){C().toast('Admin password is required to save the remote profile.',true);return}
  const checked=id=>q(id)&&q(id).checked?'1':'0';
  const value=id=>q(id)?q(id).value.trim():'';
  const data={
    password,
    mode:value('#remoteMode'),monitoring:checked('#remoteMonitoring'),management:checked('#remoteManagement'),terminal:checked('#remoteTerminal'),
    node_name:value('#remoteNodeName'),site_label:value('#remoteSiteLabel'),source_allowlist:value('#remoteAllowlist'),
    heartbeat_seconds:value('#remoteHeartbeat'),offline_seconds:value('#remoteOffline'),
    wg_endpoint:value('#wgEndpoint'),wg_port:value('#wgPort'),wg_address:value('#wgAddress'),wg_peer_public_key:value('#wgPeerKey'),
    wg_allowed_ips:value('#wgAllowedIps'),wg_keepalive:value('#wgKeepalive'),wg_dns:value('#wgDns'),wg_mtu:value('#wgMtu'),
    zt_network_id:value('#ztNetworkId')
  };
  const x=await C().api('remote_config_set',data);
  if(pass)pass.value='';
  if(!x.ok){C().toast(x.error||'Remote profile validation failed',true);return}
  // The save response is authoritative. Render it immediately so a delayed
  // follow-up status request cannot leave the operator looking at stale state.
  renderRemoteStatus(x.remote||{});
  C().toast('Remote profile validated and stored. Use the selected transport\'s Test & Apply control for live activation.');
  await loadRemote();
}
async function generateWireGuardKey(){
  ++remoteLoadGeneration;
  const pass=q('#remotePassword'),password=(pass&&pass.value)||'';
  if(!password){C().toast('Admin password is required to generate/show the device WireGuard key.',true);return}
  const x=await C().api('remote_wireguard_key',{password});
  if(pass)pass.value='';
  if(!x.ok){C().toast(x.error||'Unable to prepare WireGuard key',true);return}
  const pub=q('#wgLocalPublicKey');if(pub)pub.value=x.public_key||'';
  C().toast('WireGuard device public key is ready. Configure this public key on your hub.');
  await loadRemote();
}
async function applyWireGuard(){
  ++remoteLoadGeneration;
  const pass=q('#remotePassword'),password=(pass&&pass.value)||'';
  if(!password){C().toast('Admin password is required to apply WireGuard.',true);return}
  if(!confirm('Test and apply the staged WireGuard profile? Start this only from a local/non-WireGuard admin path. BlazePwifi will require a real handshake and automatically restore the previous network if health checks fail.'))return;
  const state=q('#remoteConfigState');if(state)state.textContent='Applying WireGuard transaction and waiting for a verified handshake…';
  const x=await C().api('remote_wireguard_apply',{password});
  if(pass)pass.value='';
  if(!x.ok){if(state)state.textContent=x.error||'WireGuard apply rolled back safely.';C().toast(x.error||'WireGuard apply failed and was rolled back',true);await loadRemote();return}
  renderRemoteStatus(x.remote||{});
  if(state)state.textContent='WireGuard is active. The previous network snapshot is no longer pending because handshake and route-survival checks passed.';
  C().toast('WireGuard activated successfully.');
  await loadRemote();
}
async function disableWireGuard(){
  ++remoteLoadGeneration;
  const pass=q('#remotePassword'),password=(pass&&pass.value)||'';
  if(!password){C().toast('Admin password is required to disable WireGuard.',true);return}
  if(!confirm('Disable the live WireGuard tunnel? This must be initiated from a local/non-WireGuard admin path.'))return;
  const state=q('#remoteConfigState');if(state)state.textContent='Disabling WireGuard transaction…';
  const x=await C().api('remote_wireguard_disable',{password});
  if(pass)pass.value='';
  if(!x.ok){if(state)state.textContent=x.error||'WireGuard disable failed safely.';C().toast(x.error||'WireGuard disable failed safely',true);await loadRemote();return}
  renderRemoteStatus(x.remote||{});
  if(state)state.textContent='Live WireGuard is disabled. The profile and device key remain staged for future use.';
  C().toast('Live WireGuard disabled.');
  await loadRemote();
}
async function prepareZeroTierIdentity(){
  ++remoteLoadGeneration;
  const pass=q('#remotePassword'),password=(pass&&pass.value)||'';
  if(!password){C().toast('Admin password is required to prepare the ZeroTier identity.',true);return}
  const x=await C().api('remote_zerotier_identity',{password});
  if(pass)pass.value='';
  if(!x.ok){C().toast(x.error||'Unable to prepare ZeroTier identity',true);return}
  const n=q('#ztNodeId');if(n)n.value=x.node_id||'';
  renderRemoteStatus(x.remote||{});
  C().toast('ZeroTier node ID is ready. Authorize this node in your ZeroTier network before applying.');
  await loadRemote();
}
async function applyZeroTier(){
  ++remoteLoadGeneration;
  const pass=q('#remotePassword'),password=(pass&&pass.value)||'';
  if(!password){C().toast('Admin password is required to apply ZeroTier.',true);return}
  if(!confirm('Test and apply the staged ZeroTier profile? Start this only from a local/non-ZeroTier admin path. The node must already be authorized. BlazePwifi will roll back automatically unless ZeroTier reaches OK with an assigned IPv4 and safe routes.'))return;
  const state=q('#remoteConfigState');if(state)state.textContent='Applying ZeroTier transaction and waiting for authorized OK state…';
  const x=await C().api('remote_zerotier_apply',{password});
  if(pass)pass.value='';
  if(!x.ok){if(state)state.textContent=x.error||'ZeroTier apply rolled back safely.';C().toast(x.error||'ZeroTier apply failed and was rolled back',true);await loadRemote();return}
  renderRemoteStatus(x.remote||{});
  if(state)state.textContent='ZeroTier is active. Network authorization, assigned IPv4, route safety and management-path survival all passed.';
  C().toast('ZeroTier activated successfully.');
  await loadRemote();
}
async function disableZeroTier(){
  ++remoteLoadGeneration;
  const pass=q('#remotePassword'),password=(pass&&pass.value)||'';
  if(!password){C().toast('Admin password is required to disable ZeroTier.',true);return}
  if(!confirm('Disable the live ZeroTier tunnel? This must be initiated from a local/non-ZeroTier admin path.'))return;
  const state=q('#remoteConfigState');if(state)state.textContent='Disabling ZeroTier transaction…';
  const x=await C().api('remote_zerotier_disable',{password});
  if(pass)pass.value='';
  if(!x.ok){if(state)state.textContent=x.error||'ZeroTier disable failed safely.';C().toast(x.error||'ZeroTier disable failed safely',true);await loadRemote();return}
  renderRemoteStatus(x.remote||{});
  if(state)state.textContent='Live ZeroTier is disabled. The stable node identity and staged profile remain available for reuse.';
  C().toast('Live ZeroTier disabled.');
  await loadRemote();
}
async function runTool(){
  const o=q('#toolOutput'),tool=q('#toolName').value,target=q('#toolTarget').value.trim();
  o.textContent='Running '+tool+'…';
  const x=await C().api('tool_run',{tool,target});
  o.textContent=x.ok?((x.output||'(no output)')+'\n\nExit code: '+x.exit_code):(x.error||'Tool failed');
  if(!x.ok)C().toast(x.error||'Tool failed',true);
}
async function loadTerminal(){
  const state=q('#terminalState'),limits=q('#terminalLimits');
  const x=await C().api('terminal_status');
  if(!x.ok){
    terminalToken='';
    if(state){state.textContent='Admin role required';state.className='badge'}
    if(limits)limits.textContent='Advanced Terminal is available only to administrators.';
    return;
  }
  if(state){state.textContent=x.enabled?'Enabled':'Disabled';state.className='badge '+(x.enabled?'good':'')}
  if(limits)limits.textContent='Active sessions '+x.active_sessions+' · TTL '+x.ttl_seconds+'s · idle '+x.idle_seconds+'s · command timeout '+x.command_timeout_seconds+'s · output cap '+x.output_max_bytes+' bytes';
  if(!x.enabled)terminalToken='';
}
async function setTerminalEnabled(enabled){
  const pass=q('#terminalPassword'),password=(pass&&pass.value)||'';
  if(!password){C().toast('Admin password is required.',true);return}
  if(enabled&&!confirm('Enable Advanced Terminal? Commands run as the router administrator and are audit logged.'))return;
  const x=await C().api('terminal_set_enabled',{enabled:enabled?'1':'0',password});
  if(pass)pass.value='';
  if(!x.ok){C().toast(x.error||'Unable to change terminal state',true);return}
  if(!enabled)terminalToken='';
  C().toast(enabled?'Advanced Terminal enabled.':'Advanced Terminal disabled and all terminal sessions closed.');
  await loadTerminal();
}
async function openTerminal(){
  const pass=q('#terminalPassword'),password=(pass&&pass.value)||'',out=q('#terminalOutput');
  if(!password){C().toast('Admin password is required to open a terminal session.',true);return}
  const x=await C().api('terminal_open',{password});
  if(pass)pass.value='';
  if(!x.ok){terminalToken='';if(out)out.textContent=x.error||'Unable to open terminal';C().toast(x.error||'Unable to open terminal',true);return}
  terminalToken=x.terminal_token||'';
  if(out)out.textContent='Terminal session opened. Token remains only in page memory. TTL '+x.ttl_seconds+'s · idle '+x.idle_seconds+'s.';
  await loadTerminal();
}
async function runTerminal(){
  const out=q('#terminalOutput'),command=q('#terminalCommand').value.trim();
  if(!terminalToken){C().toast('Open a re-authenticated terminal session first.',true);return}
  if(!command){C().toast('Enter a command.',true);return}
  if(out)out.textContent='Running bounded command…';
  const x=await C().api('terminal_exec',{terminal_token:terminalToken,command});
  if(!x.ok){
    if(/expired|invalid|disabled/i.test(String(x.error||'')))terminalToken='';
    if(out)out.textContent=x.error||'Terminal command failed';
    C().toast(x.error||'Terminal command failed',true);
    await loadTerminal();
    return;
  }
  if(out)out.textContent=(x.output||'(no output)')+'\n\nExit code: '+x.exit_code;
}
async function closeTerminal(){
  const out=q('#terminalOutput');
  if(!terminalToken){if(out)out.textContent='No terminal session is open.';return}
  const token=terminalToken;terminalToken='';
  const x=await C().api('terminal_close',{terminal_token:token});
  if(out)out.textContent=x.ok?'Terminal session closed.':(x.error||'Terminal session closed locally; server close failed.');
  await loadTerminal();
}
async function loadUpdate(){
  const x=await C().api('update_status');
  if(!x.ok){C().toast(x.error||'Update status unavailable',true);return}
  const s=x.state||{};
  const set=(id,val,good)=>{const n=q(id);if(n){n.textContent=val||'—';n.className='badge '+(good?'good':'');}};
  set('#updateCurrent',s.current,false);
  set('#updateStable',s.stable,true);
  set('#updatePending',s.pending||'None',false);
  set('#updateRollback',s.rollback||'None',!!s.rollback_available);
  const src=q('#updateSource'); if(src)src.textContent='Configured source: '+(x.source_url||'not configured');
}
async function installUpdate(){
  const url=(q('#updateUrl').value||'').trim(),sha=(q('#updateSha').value||'').trim();
  if(!/^https:\/\//i.test(url)){C().toast('HTTPS update URL required',true);return}
  if(!/^[0-9a-f]{64}$/i.test(sha)){C().toast('Exact SHA-256 required',true);return}
  if(!confirm('Install this verified update? BlazePwifi will preserve the current stable files for rollback.'))return;
  const x=await C().api('update_apply_url',{url,sha256:sha});
  if(!x.ok){C().toast(x.error||'Update failed',true);await loadUpdate();return}
  C().toast('Update installed as a pending candidate. Previous stable version is preserved.');
  await loadUpdate(); await loadSystem();
}
async function rollbackUpdate(){
  if(!confirm('Roll back to the preserved previous stable BlazePwifi version?'))return;
  const x=await C().api('update_rollback',{});
  if(!x.ok){C().toast(x.error||'Rollback failed',true);await loadUpdate();return}
  C().toast('Rollback complete.');
  await loadUpdate(); await loadSystem();
}
async function loadLan(){
  const keys=['lan_if','management_if','hotspot_if','management_vlan','hotspot_vlan','controller_vlan','rental_vlan'];
  const vals=[];
  for(const key of keys){const x=await C().api('config_get',{key});if(x.ok)vals.push(key+'='+x.value)}
  const n=q('#lanConfig');if(n)n.textContent=vals.join(' • ')||'No network assignment reported.';
}
function onPage(name){
  if(name==='system'||name==='wan')loadSystem();
  if(name==='storage')loadStorage();
  if(name==='updates')loadUpdate();
  if(name==='remote')loadRemote();
  if(name==='tools')loadTerminal();
  if(name==='lan')loadLan();
}
window.BlazeConsole={loadSystem,loadStorage,loadRemote,saveRemote,generateWireGuardKey,applyWireGuard,disableWireGuard,prepareZeroTierIdentity,applyZeroTier,disableZeroTier,runTool,loadTerminal,setTerminalEnabled,openTerminal,runTerminal,closeTerminal,loadLan,loadUpdate,installUpdate,rollbackUpdate,onPage};
// Do not preload editable Remote Access configuration in the background.
 // It is loaded on page entry/explicit refresh so a delayed startup request
 // cannot overwrite operator edits.
setTimeout(()=>{loadSystem();},300);
})();