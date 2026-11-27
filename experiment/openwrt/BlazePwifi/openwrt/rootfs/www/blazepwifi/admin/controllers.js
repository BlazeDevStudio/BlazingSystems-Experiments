(function(){
'use strict';
const q=s=>document.querySelector(s), C=()=>window.BlazeCore;

function checked(v){return (+v)!==0?'checked':''}
function val(v,fallback){return C().esc(v==null?fallback:v)}
function node(id){return document.querySelector('[data-controller="'+CSS.escape(id)+'"]')}

function card(x){
  const raw=String(x.id||''), id=C().esc(raw);
  const online=(+x.last_seen||0)>(Math.floor(Date.now()/1000)-30);
  return '<div class="card device-card" data-controller="'+id+'">'+
    '<div class="device-top"><div><div class="device-name">'+id+'</div>'+
    '<div class="device-meta">'+C().esc(x.ip||'No IP reported')+'</div></div>'+
    '<div class="toolbar"><span class="badge '+(online?'good':'bad')+'">'+(online?'ONLINE':'OFFLINE')+'</span>'+
    '<span class="badge">rev '+val(x.config_revision,0)+'</span></div></div>'+
    '<div class="switch-row"><span><b>Controller enabled</b><div class="small muted">Master switch for this coinslot controller</div></span><input class="toggle enabled" type="checkbox" '+checked(x.enabled)+'></div>'+
    '<div class="switch-row"><span>Coin input enabled</span><input class="toggle coinEnabled" type="checkbox" '+checked(x.coin_enabled)+'></div>'+
    '<div class="switch-row"><span>Relay output enabled</span><input class="toggle relayEnabled" type="checkbox" '+checked(x.relay_enabled)+'></div>'+
    '<div class="switch-row"><span>LED output enabled</span><input class="toggle ledEnabled" type="checkbox" '+checked(x.led_enabled)+'></div>'+
    '<div class="form-grid" style="margin-top:14px">'+
      '<label><span class="field-label">Coin GPIO</span><input class="field coinPin" inputmode="numeric" value="'+val(x.coin_pin,-1)+'"></label>'+
      '<label><span class="field-label">Relay GPIO</span><input class="field relayPin" inputmode="numeric" value="'+val(x.relay_pin,-1)+'"></label>'+
      '<label><span class="field-label">LED GPIO</span><input class="field ledPin" inputmode="numeric" value="'+val(x.led_pin,-1)+'"></label>'+
      '<label><span class="field-label">Debounce ms</span><input class="field debounce" inputmode="numeric" value="'+val(x.coin_debounce_ms,40)+'"></label>'+
      '<label><span class="field-label">Pulse group ms</span><input class="field pulseGroup" inputmode="numeric" value="'+val(x.pulse_group_ms,400)+'"></label>'+
      '<label><span class="field-label">Max Wi-Fi retries</span><input class="field retries" inputmode="numeric" value="'+val(x.max_wifi_retries,6)+'"></label>'+
    '</div>'+
    '<div class="switch-row"><span>Coin input active-low</span><input class="toggle coinLow" type="checkbox" '+checked(x.coin_active_low)+'></div>'+
    '<div class="switch-row"><span>Relay output active-high</span><input class="toggle relayHigh" type="checkbox" '+checked(x.relay_active_high)+'></div>'+
    '<div class="switch-row"><span>LED output active-high</span><input class="toggle ledHigh" type="checkbox" '+checked(x.led_active_high)+'></div>'+
    '<div class="device-actions"><button class="btn primary sm" onclick="BlazeControllers.save(\''+id+'\')">Save controller</button></div>'+
    '<div class="small muted" style="margin-top:10px">Last seen '+(x.last_seen?new Date(x.last_seen*1000).toLocaleString():'never')+
      ' • Settings are delivered on the next controller poll.</div></div>';
}

async function load(render=true){
  const x=await C().api('controller_list');
  if(!x.ok){if(render)C().toast(x.error||'Controller load failed',true);return}
  const items=x.controllers||[];
  if(render)q('#controllerCards').innerHTML=items.length?items.map(card).join(''):'<div class="card empty">No coin controllers registered yet.</div>';
}

async function save(id){
  const n=node(id); if(!n)return;
  const data={
    id,
    enabled:n.querySelector('.enabled').checked?'1':'0',
    coin_enabled:n.querySelector('.coinEnabled').checked?'1':'0',
    relay_enabled:n.querySelector('.relayEnabled').checked?'1':'0',
    led_enabled:n.querySelector('.ledEnabled').checked?'1':'0',
    coin_pin:n.querySelector('.coinPin').value.trim(),
    relay_pin:n.querySelector('.relayPin').value.trim(),
    led_pin:n.querySelector('.ledPin').value.trim(),
    coin_active_low:n.querySelector('.coinLow').checked?'1':'0',
    relay_active_high:n.querySelector('.relayHigh').checked?'1':'0',
    led_active_high:n.querySelector('.ledHigh').checked?'1':'0',
    coin_debounce_ms:n.querySelector('.debounce').value.trim(),
    pulse_group_ms:n.querySelector('.pulseGroup').value.trim(),
    max_wifi_retries:n.querySelector('.retries').value.trim()
  };
  const x=await C().api('controller_set',data);
  C().toast(x.ok?'Controller settings saved':(x.error||'Controller update failed'),!x.ok);
  if(x.ok)load();
}
window.BlazeControllers={load,save};
})();