'use strict';
// A source map built ONLY from generator-owned setup/loop/function statements.
// User-owned C++ and manual mode are never scanned or attributed to visual blocks.
function flowIds(flow){const ids=new Set();function visit(steps){for(const x of steps||[]){ids.add(x.id);visit(x.thenSteps);visit(x.elseSteps);}}visit(flow?.steps);return ids;}
function sourceAttribution(source,project,{setup=[],loop=[],graphLoop=[]}={}){
 if(project?.source?.mode==='manual'||typeof source!=='string')return [];
 const lines=source.split('\n'),nodes=new Set((project.graph?.nodes||[]).map(x=>x.id)),flows=flowIds(project.flowchart);
 const result=[];
 function lastBefore(header,end){let bound=lines.findIndex(x=>x===end);if(bound<0)throw Error('Missing generated source section: '+end);for(let i=bound-1;i>=0;i--)if(lines[i]===header)return i+1;throw Error('Missing generated function header: '+header);}
 function add(section,emitted,start){let row=start;
  for(const statement of emitted){for(const line of String(statement).split('\n')){
   if(lines[row]!==line)throw Error('Generated source map line mismatch in '+section+' at '+(row+1));
   const marker=line.match(/\/\/\s*(node|flow):([A-Za-z0-9_-]+)(?:\s|$)/);
   if(marker&&(marker[1]==='node'?nodes:flows).has(marker[2]))result.push({kind:marker[1],id:marker[2],line:row+1,section,code:line.trim()});
   row++;
  }}
 }
 const setupStart=lastBefore('void setup() {','// BEGIN USER SETUP');
 const loopStart=lastBefore('void loop() {','// BEGIN USER LOOP');
 add('setup',setup,setupStart);add('loop',loop,loopStart);
 if(graphLoop.length){let functionStart=-1;for(let i=setupStart-1;i>=0;i--)if(lines[i]==='void blazeNodesTick() {'){functionStart=i+1;break;}
  if(functionStart<0)throw Error('Missing generated node function header');add('nodes',graphLoop,functionStart);
 }
 return result.sort((a,b)=>a.line-b.line);
}
module.exports={sourceAttribution};
