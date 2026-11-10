'use strict';
// This registry intentionally covers only classic ESP32 and the ESP8266 generic/NodeMCU
// Arduino targets. Electrical access and breakout-pin existence vary by module/carrier.
const RE=/^[\w.-]+:[\w.-]+:[\w.-]+(?::[\w.,=~-]+)?$/;
const range=(a,b)=>Array.from({length:b-a+1},(_,i)=>String(a+i));
const PROFILES=Object.freeze({
 'arduino:avr:uno':{
  provenance:'Arduino Uno Rev3 ATmega328P official pinout',sourceUrl:'https://docs.arduino.cc/hardware/uno-rev3/',
  scope:'Uno R3 basic digital and PWM only; physical shield wiring unverified',
  pins:range(0,13),inputOnly:[],blocked:[],bootSensitive:[],serial:['0','1'],pwm:['3','5','6','9','10','11'],safeDefault:'13',analog:range(0,5).map(n=>'A'+n),voltage:'5V logic'
 },
 'esp8266:esp8266:generic':{
  provenance:'ESP8266 Arduino Core Digital IO Reference',sourceUrl:'https://arduino-esp8266.readthedocs.io/en/latest/reference.html',
  scope:'Generic ESP8266 silicon GPIO; flash wiring and carrier breakout are module dependent',
  pins:[...range(0,5),...range(12,16)],inputOnly:[],blocked:range(6,11),bootSensitive:['0','2','15'],serial:['1','3'],pwm:['0','1','2','3','4','5','12','13','14','15'],safeDefault:'4',analog:['A0'],voltage:'3.3V logic'
 },
 'esp8266:esp8266:nodemcuv2':{
  provenance:'ESP8266 Arduino Core Digital IO Reference; NodeMCU v1.0 ESP-12E',sourceUrl:'https://arduino-esp8266.readthedocs.io/en/latest/reference.html',
  scope:'Raw GPIO numbering rather than silk-screen D aliases; module wiring must be checked',
  pins:[...range(0,5),...range(12,16)],inputOnly:[],blocked:range(6,11),bootSensitive:['0','2','15'],serial:['1','3'],pwm:['0','1','2','3','4','5','12','13','14','15'],safeDefault:'4',analog:['A0'],voltage:'3.3V logic'
 },
 'esp32:esp32:esp32':{
  provenance:'Espressif ESP32-DevKitC-1 Pin Layout and ESP32 Datasheet',sourceUrl:'https://docs.espressif.com/projects/arduino-esp32/en/latest/boards/ESP32-DevKitC-1.html',
  scope:'Classic ESP32 only; NOT ESP32-S2/S3/C3/C6/H2/P4; flash/PSRAM and carrier restrictions vary',
  pins:[...range(0,5),...range(12,19),...range(21,23),...range(25,27),...range(32,39)],
  inputOnly:range(34,39),blocked:range(6,11),bootSensitive:['0','2','4','5','12','15'],serial:['1','3'],
  // Curated conservative PWM subset; not a claim that other SoC GPIO lack LEDC support.
  pwm:['13','14','18','19','21','22','23','25','26','27','32','33'],safeDefault:'21',analog:['32','33','34','35','36','39'],voltage:'3.3V logic'
 }
});
function profile(fqbn){return PROFILES[fqbn]||null;}
function pinCheck(fqbn,pin,operation='output'){
 const model=profile(fqbn),p=String(pin),errors=[],warnings=[];
 if(!model){warnings.push(`GPIO ${p}: Unknown / Verification Required for ${fqbn}`);return {errors,warnings,profile:null};}
 if(model.blocked.includes(p)){errors.push(`GPIO ${p} is reserved for flash or restricted on ${fqbn}`);return {errors,warnings,profile:model};}
 if(!model.pins.includes(p)){errors.push(`GPIO ${p} is not in the curated usable pin set for ${fqbn}`);return {errors,warnings,profile:model};}
 if(operation!=='input'&&model.inputOnly.includes(p))errors.push(`GPIO ${p} is input-only on ${fqbn}; cannot drive outputs`);
 if(operation==='pullup'&&(model.inputOnly.includes(p)||(fqbn.startsWith('esp8266:')&&p==='16')))errors.push(`GPIO ${p} has no internal pull-up on ${fqbn}`);
 if(operation==='pwm'&&!model.pwm.includes(p))errors.push(`GPIO ${p} not in validated PWM subset for ${fqbn}`);
 if(model.bootSensitive.includes(p))warnings.push(`GPIO ${p} is bootstrapping-sensitive on ${fqbn}; external circuitry can prevent boot`);
 if(model.serial.includes(p))warnings.push(`GPIO ${p} shares UART on ${fqbn}`);
 warnings.push(`${fqbn}: ${model.scope}; ${model.voltage}; compilation cannot prove safe physical wiring`);
 return {errors,warnings,profile:model};
}
function analyzeBoardChange(project,target){
 if(!RE.test(target))throw Error('Invalid target FQBN');const before=profile(project.fqbn),after=profile(target),issues=[],warnings=[];
 const active=(project.graph?.nodes||[]).filter(n=>['pinMode','digitalWrite','pwmWrite','thresholdOutput'].includes(n.type)).map(n=>({id:n.id,pin:String(n.params.pin),op:n.type==='pinMode'&&n.params.mode==='INPUT'?'input':'output'}));
 const visit=list=>{for(const n of list||[]){if(['setOutput','write','branch'].includes(n.type))active.push({id:n.id,pin:String(n.params.pin),op:n.type==='branch'?'input':'output'});visit(n.thenSteps);visit(n.elseSteps);}};visit(project.flowchart?.steps);
 for(const pin of active){const check=pinCheck(target,pin.pin,pin.op);issues.push(...check.errors.map(e=>pin.id+': '+e));warnings.push(...check.warnings.map(w=>pin.id+': '+w));}
 if(project.libraryDependencies?.length)warnings.push('Library compatibility needs re-analysis for new architecture');
 if(project.graph?.nodes?.some(n=>['readAnalog','thresholdOutput','wireWrite'].includes(n.type))&&target!=='arduino:avr:uno')issues.push('Uno-specific compiled adapters require replacement or independent target validation');
 return {from:project.fqbn,to:target,compatible:issues.length===0&&warnings.length===0,issues:[...new Set(issues)],warnings:[...new Set(warnings)],oldProfile:before?.provenance||'Unknown',newProfile:after?.provenance||'Unknown / Verification Required',requiresSnapshot:true};
}
module.exports={RE,PROFILES,profile,pinCheck,analyzeBoardChange};
