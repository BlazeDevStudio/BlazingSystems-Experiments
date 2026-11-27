#!/bin/sh
# UI-0638: actual BlazeMembers UI source behavior under synthetic browser APIs.
# No browser network or customer data; node VM never has remote HTTP access.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
UI="$ROOT/openwrt/rootfs/www/blazepwifi/admin/members.js"
node --check "$UI"
node - "$UI" <<'JS'
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
let bank=180,deletes=0,confirms=0,memberCalls=0;
const toasts=[];
const elements={
  '#memberCards': {innerHTML:''},
  '#memberRevision': {textContent:''},
  '#memberEvents': {textContent:''},
};
global.document={querySelector:(selector)=>elements[selector]||null};
global.confirm=()=>{confirms++;return true};
global.window={BlazeCore:{
  esc:(x)=>String(x),
  toast:(message,error)=>toasts.push({message,error}),
  api:async(action)=>{
    if(action==='member_list'){
      memberCalls++;
      return {ok:true,revision:1,members:[{username:'alice',label:'Synthetic',enabled:1,revision:1,banked_seconds:bank}]};
    }
    if(action==='member_delete'){deletes++;return {ok:true}}
    if(action==='member_events')return {ok:true,events:[]};
    throw new Error('Unexpected UI API call: '+action);
  }
}};
vm.runInThisContext(fs.readFileSync(process.argv[2],'utf8'),{filename:'members.js'});
(async()=>{
  await window.BlazeMembers.load();
  assert.match(elements['#memberCards'].innerHTML,/disabled aria-disabled="true"/);
  assert.match(elements['#memberCards'].innerHTML,/Deletion blocked: transfer or settle remaining banked time first/);
  await window.BlazeMembers.remove('alice');
  assert.strictEqual(deletes,0,'nonzero paid time was submitted for deletion');
  assert.strictEqual(confirms,0,'no confirmation should ask to forfeit positive paid time');
  assert(toasts.some(x=>/transfer or settle banked paid time/.test(x.message)));

  bank=0;
  await window.BlazeMembers.load();
  assert(!elements['#memberCards'].innerHTML.includes('disabled aria-disabled="true"'));
  await window.BlazeMembers.remove('alice');
  assert.strictEqual(deletes,1,'zero-balance delete not forwarded to authenticated backend');
  assert.strictEqual(confirms,1);

  // On a stale rendered zero-balance card, the member gets fresh banked time
  // from another controller; recheck must refuse the destructive API call.
  bank=0;await window.BlazeMembers.load();
  bank=240;
  await window.BlazeMembers.remove('alice');
  assert.strictEqual(deletes,1,'stale zero-balance DOM caused paid credit loss');
  assert.strictEqual(confirms,1,'stale zero-balance triggered false confirmation');

  bank='corrupt';
  await window.BlazeMembers.remove('alice');
  assert.strictEqual(deletes,1,'corrupt balance was interpreted as zero');
  assert(memberCalls>=5,'member snapshot was not rechecked before deletion');
  console.log('UI-0638 PASS: paid Delete disabled, action guidance, fresh balance checked, stale DOM and corrupt balance fail closed');
})().catch(e=>{console.error(e);process.exit(1)});
JS
