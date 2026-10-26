'use strict';
// Deterministic typed state for visual firmware. There is deliberately no arbitrary expression parser.
const IDENT=/^[A-Za-z][A-Za-z0-9_]{0,39}$/;
const TYPES=new Set(['long','float','bool']);
const RESERVED=new Set(['setup','loop','HIGH','LOW','true','false','Serial','Wire','pinMode','digitalWrite','analogRead','analogWrite']);
const INT_RE=/^-?(?:0|[1-9][0-9]*)$/;
const FLOAT_RE=/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,8})?$/;
function literal(type,raw){
 const text=String(raw??'').trim();
 if(type==='bool'){if(text!=='true'&&text!=='false')throw Error('Boolean values must be true or false');return text;}
 if(type==='long'){
  if(!INT_RE.test(text))throw Error('Integer value must be a decimal literal');
  const n=Number(text);if(!Number.isSafeInteger(n)||n < -2147483648||n > 2147483647)throw Error('Integer must fit signed 32-bit');
  return `${n}L`;
 }
 if(type==='float'){
  if(!FLOAT_RE.test(text))throw Error('Float value must be a finite decimal literal');
  const n=Number(text);if(!Number.isFinite(n)||Math.abs(n)>1000000)throw Error('Float literal must be within +/-1000000');
  return `${text.includes('.')?text:text+'.0'}f`;
 }
 throw Error('Unsupported variable type');
}
function validate(variables){
 const errors=[],names=new Set(),entries=variables===undefined?[]:variables;
 if(!Array.isArray(entries)||entries.length>64)return {errors:['Variables must be an array of at most 64 declarations'],map:new Map()};
 const map=new Map();
 for(const v of entries){
  if(!v||typeof v!=='object'||!IDENT.test(v.name||'')||RESERVED.has(v.name)||!TYPES.has(v.type)){errors.push('Invalid variable declaration or reserved name');continue;}
  if(names.has(v.name)){errors.push(`Duplicate variable: ${v.name}`);continue;}
  names.add(v.name);
  try{literal(v.type,v.initial);map.set(v.name,v);}catch(e){errors.push(`${v.name}: ${e.message}`);}
 }
 return {errors,map};
}
function symbol(name){if(!IDENT.test(name||'')||RESERVED.has(name))throw Error('Invalid variable name');return 'blazeVar_'+name;}
function writeTarget(n,variables){const v=variables.get(n.params.target);if(!v)throw Error(`${n.id}: variable '${n.params.target}' is not declared`);return v;}
function checkNode(n,variables,board){
 const errors=[],warnings=[],p=n.params||{};let v;
 try{
  if(n.type==='setVariable') {v=writeTarget(n,variables);literal(v.type,p.value);}
  if(n.type==='readAnalog') {
   v=writeTarget(n,variables);
   if(v.type!=='long')throw Error(`${n.id}: analog reading requires long variable`);
   if(board!=='arduino:avr:uno')throw Error(`${n.id}: A0–A5 read only validated on Uno R3`);
   if(!/^A[0-5]$/.test(p.pin||''))throw Error(`${n.id}: analog input must be A0–A5`);
  }
  if(n.type==='thresholdOutput') {
   v=writeTarget({...n,params:{target:p.variable}},variables);
   if(v.type==='bool')throw Error(`${n.id}: threshold requires numeric variable`);
   if(!['<','<=','>','>=','==','!='].includes(p.operator))throw Error(`${n.id}: invalid comparison operator`);
   literal(v.type,p.threshold);
   if(board!=='arduino:avr:uno')throw Error(`${n.id}: output pin model only validated on Uno R3`);
   if(!/^\d{1,2}$/.test(String(p.pin))||Number(p.pin)>13)throw Error(`${n.id}: output pin must be Uno D0–D13`);
   if(!['HIGH','LOW'].includes(p.trueValue)||!['HIGH','LOW'].includes(p.falseValue))throw Error(`${n.id}: invalid output level`);
   if(Number(p.pin)<2)warnings.push(`${n.id}: D0/D1 share hardware Serial`);
  }
 }catch(e){errors.push(e.message);}
 return {errors,warnings};
}
function emit(n,variables){const p=n.params;
 if(n.type==='setVariable'){const v=variables.get(p.target);return {loop:[`  ${symbol(v.name)} = ${literal(v.type,p.value)}; // node:${n.id}`],setup:[]};}
 if(n.type==='readAnalog')return {loop:[`  ${symbol(p.target)} = analogRead(${p.pin}); // node:${n.id}`],setup:[]};
 if(n.type==='thresholdOutput'){
  const v=variables.get(p.variable);return {setup:[`  pinMode(${Number(p.pin)}, OUTPUT); // node:${n.id}`],loop:[`  digitalWrite(${Number(p.pin)}, (${symbol(p.variable)} ${p.operator} ${literal(v.type,p.threshold)}) ? ${p.trueValue} : ${p.falseValue}); // node:${n.id}`]};
 }
 return {setup:[],loop:[]};
}
function declarations(vars){return vars.map(v=>`${v.type} ${symbol(v.name)} = ${literal(v.type,v.initial)};`).join('\n');}
function initialState(vars){return Object.fromEntries(vars.map(v=>[v.name,v.type==='bool'?v.initial==='true':Number(v.initial)]));}
module.exports={validate,literal,symbol,checkNode,emit,declarations,initialState};
