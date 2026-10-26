'use strict';
// Curated Wire adapter. Never infer executable semantics from header scanning alone.
const UNO='arduino:avr:uno';
const BYTE=/^(?:\d{1,3}|0x[0-9a-fA-F]{1,2})$/;
function asByte(raw,label,min=0,max=255){const s=String(raw??'');if(!BYTE.test(s))throw Error(`${label}: use decimal or 0x hex`);const n=s.startsWith('0x')?parseInt(s.slice(2),16):Number(s);if(!Number.isInteger(n)||n<min||n>max)throw Error(`${label}: must be ${min}..${max}`);return n;}
function validate(n,fqbn){const errors=[],warnings=[];if(fqbn!==UNO)errors.push(`${n.id}: Wire register adapter only compile-gated on Arduino Uno; other targets require validation`);for(const [key,min,max] of [['address',8,119],['register',0,255],['value',0,255]])try{asByte(n.params[key],key,min,max);}catch(e){errors.push(`${n.id}: ${e.message}`)}if(!errors.length)warnings.push(`${n.id}: Wire is compile-gated only; device voltage, ACK and electrical behavior unverified`);return {errors,warnings};}
function emit(n){const p=n.params,a=asByte(p.address,'address',8,119),r=asByte(p.register,'register'),v=asByte(p.value,'value');return [`  Wire.beginTransmission((uint8_t)${a}); // node:${n.id}`,`  Wire.write((uint8_t)${r});`,`  Wire.write((uint8_t)${v});`,`  blazeLastWireStatus = Wire.endTransmission();`];}
module.exports={asByte,validate,emit,descriptor:{name:'Wire I2C register write',type:'wireWrite',fqbn:UNO,library:'Wire',evidence:'Uno core Wire.h; compile gate required',confidence:'curated'}};
