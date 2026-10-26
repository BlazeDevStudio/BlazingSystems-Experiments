"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const html = fs.readFileSync(path.join(__dirname,"../app/src/main/assets/fixture.html"),"utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match,"fixture must include the real observation script");
function harness() {
  const nodes = [
    {dataset:{id:"fx-1",sender:"Inspector"},textContent:"Have the inspection photos arrived?"},
    {dataset:{id:"fx-2",sender:"You"},textContent:"I am reviewing the hatch images."}
  ];
  let mutation=()=>{};
  const snapshots=[];
  const root={
    querySelectorAll(selector){ assert.equal(selector,".message"); return nodes; },
    appendChild(node){ nodes.push(node);mutation(); }
  };
  const context={
    document:{
      querySelector(selector){assert.equal(selector,"#messages");return root;},
      createElement(tag){assert.equal(tag,"p");return {className:"",dataset:{},textContent:""};}
    },
    MutationObserver:class{constructor(callback){mutation=callback;}observe(){}},
    setTimeout,
    HarborBridge:{postMessage(raw){snapshots.push(JSON.parse(raw));}}
  };
  context.window=context;
  vm.runInNewContext(match[1],context,{timeout:1000,filename:"fixture.html"});
  return {context,nodes,snapshots};
}
const tick=()=>new Promise(resolve=>setTimeout(resolve,110));
const id1="11111111-1111-4111-8111-111111111111";
const id2="22222222-2222-4222-8222-222222222222";
test("fixture emits original DOM messages as a normalized snapshot",async()=>{
  const h=harness();await tick();
  assert.equal(h.snapshots.length,1);
  assert.equal(h.snapshots[0].type,"snapshot");
  assert.equal(h.snapshots[0].adapter,"fixture-v1");
  assert.equal(h.snapshots[0].messages.length,2);
});
test("native action becomes one observable outgoing DOM message",async()=>{
  const h=harness();await tick();
  assert.equal(h.context.harborAction(JSON.stringify({action:"send",id:id1,text:"Hatch 2 complete"})),true);
  await tick();
  assert.equal(h.snapshots.at(-1).messages.at(-1).text,"Hatch 2 complete");
  assert.equal(h.snapshots.at(-1).messages.at(-1).sender,"You");
  assert.equal(h.snapshots.at(-1).messages.at(-1).id,id1);
});
test("duplicate action id does not duplicate message",async()=>{
  const h=harness();
  const req=JSON.stringify({action:"send",id:id1,text:"one"});
  assert.equal(h.context.harborAction(req),true);
  assert.equal(h.context.harborAction(req),false);
  assert.equal(h.nodes.length,3);
});
test("invalid action input fails closed",async()=>{
  const h=harness();
  for(const request of ["invalid json",JSON.stringify({action:"delete",id:id1,text:"x"}),
    JSON.stringify({action:"send",id:"bad",text:"x"}),
    JSON.stringify({action:"send",id:id1,text:""}),
    JSON.stringify({action:"send",id:id1,text:"x".repeat(4097)})]){
      assert.equal(h.context.harborAction(request),false);
  }
  assert.equal(h.nodes.length,2);
});
test("text is not interpreted as HTML",async()=>{
  const h=harness();
  const injection='<img src=x onerror=alert(1)>';
  assert.equal(h.context.harborAction(JSON.stringify({action:"send",id:id1,text:injection})),true);
  await tick();
  assert.equal(h.nodes.at(-1).textContent,injection);
  assert.equal(h.snapshots.at(-1).messages.at(-1).text,injection);
});
test("rapid DOM updates coalesce into one observer event",async()=>{
  const h=harness();await tick();
  assert.equal(h.context.harborAction(JSON.stringify({action:"send",id:id1,text:"first"})),true);
  assert.equal(h.context.harborAction(JSON.stringify({action:"send",id:id2,text:"second"})),true);
  await tick();
  assert.equal(h.snapshots.length,2);
  assert.equal(h.snapshots.at(-1).messages.length,4);
});
