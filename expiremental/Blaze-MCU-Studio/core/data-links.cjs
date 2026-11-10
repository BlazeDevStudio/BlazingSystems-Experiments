'use strict';
// Explicit scalar data sockets for the current linear execution graph.
// This is NOT an arbitrary C++ reverse parser, dynamic expression evaluator, or MCU emulator.
const PRODUCERS=new Set(['readAnalog','setVariable']);
const CONSUMERS=new Set(['thresholdOutput']);
function validateShape(graph){
 const edges=graph.dataEdges===undefined?[]:graph.dataEdges;
 if(!Array.isArray(edges)||edges.length>150)throw Error('Data connections must be a list of at most 150');
 for(const edge of edges){
  if(!edge||typeof edge!=='object'||Array.isArray(edge)||Object.keys(edge).some(k=>!['from','to','out','input'].includes(k))||
   !['from','to','out','input'].every(k=>typeof edge[k]==='string'&&/^[A-Za-z0-9_-]{1,60}$/.test(edge[k])))throw Error('Malformed typed data connection');
 }
 return edges;
}
function plan(project,ordered){
 const errors=[],bindings=new Map(),links=validateShape(project.graph);
 const positions=new Map(ordered.map((node,i)=>[node.id,i]));
 const nodes=new Map(project.graph.nodes.map(n=>[n.id,n]));
 const types=new Map((project.variables||[]).map(v=>[v.name,v.type]));
 const occupied=new Set();
 for(const e of links){
  const source=nodes.get(e.from),target=nodes.get(e.to);
  if(!source||!target){errors.push(`Data link ${e.from} → ${e.to}: endpoint missing`);continue;}
  if(!PRODUCERS.has(source.type)||e.out!=='value'||!CONSUMERS.has(target.type)||e.input!=='measurement'){
   errors.push(`Data link ${e.from} → ${e.to}: unsupported socket or direction`);continue;
  }
  if(occupied.has(target.id)){errors.push(`${target.id}: multiple wires cannot drive one measurement input`);continue;}
  occupied.add(target.id);
  if(!positions.has(source.id)||!positions.has(target.id)||positions.get(source.id)>=positions.get(target.id)){
   errors.push(`Data link ${e.from} → ${e.to}: producer must execute before consumer in active graph`);continue;
  }
  const variable=source.params?.target,type=types.get(variable);
  if(!type){errors.push(`${source.id}: data output has no declared variable`);continue;}
  if(!['long','float'].includes(type)){
   errors.push(`${source.id}: ${type} output is incompatible with numeric measurement input`);continue;
  }
  bindings.set(target.id,{source:source.id,variable,type});
 }
 return {ok:errors.length===0,errors,bindings,edges:links};
}
function effectiveNode(n,planResult){
 const binding=planResult.bindings.get(n.id);
 if(!binding)return n;
 return {...n,params:{...n.params,variable:binding.variable}};
}
module.exports={validateShape,plan,effectiveNode};
