'use strict';
// A source map built ONLY from generator-owned setup/loop/function statements.
// User-owned C++ and manual mode are never scanned or attributed to visual blocks.
function flowIds(flow){const ids=new Set();function visit(steps){for(const x of steps||[]){ids.add(x.id);visit(x.thenSteps);visit(x.elseSteps);}}visit(flow?.steps);return ids;}
function sourceAttribution(source,project,{setup=[],loop=[],graphLoop=[],offsets={}}={}){
 if(project?.source?.mode==='manual'||typeof source!=='string')return [];
 const lines=source.split('\n'),nodes=new Set((project.graph?.nodes||[]).map(x=>x.id)),flows=flowIds(project.flowchart);
 const result=[];
 function rowAt(offset,section){
  if(!Number.isSafeInteger(offset)||offset<0||offset>source.length||offset>0&&source[offset-1]!=='\n')throw Error('Invalid source mapping offset for '+section);
  return source.slice(0,offset).split('\n').length-1;
 }
 function add(section,emitted,start){let row=start;
  for(const statement of emitted){for(const line of String(statement).split('\n')){
   if(lines[row]!==line)throw Error('Generated source map line mismatch in '+section+' at '+(row+1));
   const marker=line.match(/\/\/\s*(node|flow):([A-Za-z0-9_-]+)(?:\s|$)/);
   if(marker&&(marker[1]==='node'?nodes:flows).has(marker[2]))result.push({kind:marker[1],id:marker[2],line:row+1,section,code:line.trim()});
   row++;
  }}
 }
 const setupStart=rowAt(offsets.setup,'setup'),loopStart=rowAt(offsets.loop,'loop');
 add('setup',setup,setupStart);add('loop',loop,loopStart);
 if(graphLoop.length)add('nodes',graphLoop,rowAt(offsets.nodes,'nodes'));
 return result.sort((a,b)=>a.line-b.line);
}
module.exports={sourceAttribution};
