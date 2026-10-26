'use strict';
// Resource planner, not an electrical safety certificate or auto-hardware driver.
const {profile}=require('./board.cjs');
const UNO={i2c:{sda:'A4',scl:'A5'},spi:{sck:'13',miso:'12',mosi:'11'}};
const PIN_RE=/^(?:\d{1,3}|A[0-5])$/;
function plan(project){
 const peripherals=project.peripherals||[];if(!Array.isArray(peripherals)||peripherals.length>40)throw Error('Invalid peripheral catalog');
 const errors=[],warnings=[],assignments=[],i2cAddress=new Map(),pinUsage=new Map();const board=profile(project.fqbn);
 for(const p of peripherals){
  if(!p||typeof p.id!=='string'||!/^[\w-]{1,50}$/.test(p.id)||!['i2c','spi','gpio'].includes(p.type)||!p.pins||typeof p.pins!=='object'||Array.isArray(p.pins))throw Error('Invalid peripheral assignment');
  const bus=String(p.bus||'default');if(bus.length>60)throw Error('Invalid bus identifier');
  const spec=Object.entries(p.pins);if(spec.length>8)throw Error('Too many peripheral pins');
  for(const [role,raw] of spec){const pin=String(raw);if(!PIN_RE.test(pin))errors.push(`${p.id}: invalid pin ${pin}`);
   if(!board)warnings.push(`${p.id}: ${pin} electrical/peripheral mapping Unknown / Verification Required on ${project.fqbn}`);
   else if(p.type==='gpio'&&!board.pins.includes(pin))errors.push(`${p.id}: pin ${pin} not verified for direct GPIO on ${project.fqbn}`);
   if(p.type==='i2c'&&project.fqbn==='arduino:avr:uno'&&UNO.i2c[role.toLowerCase()]!==pin)warnings.push(`${p.id}: Uno Wire hardware I2C typically uses SDA A4 and SCL A5; verify alternate implementation`);
   if(p.type==='spi'&&project.fqbn==='arduino:avr:uno'&&UNO.spi[role.toLowerCase()]&&UNO.spi[role.toLowerCase()]!==pin)warnings.push(`${p.id}: Uno SPI ${role} normally uses D${UNO.spi[role.toLowerCase()]}; verify software SPI or board variant`);
   const shared=(p.type==='i2c'&&['sda','scl'].includes(role.toLowerCase()))||(p.type==='spi'&&['sck','miso','mosi'].includes(role.toLowerCase()));
   const usage={id:p.id,type:p.type,role:role.toLowerCase(),pin,bus,shared};assignments.push(usage);let users=pinUsage.get(pin)||[];users.push(usage);pinUsage.set(pin,users);
  }
  if(p.type==='i2c'&&p.address!=null){const addr=Number(p.address);if(!Number.isInteger(addr)||addr<0x08||addr>0x77)errors.push(`${p.id}: I2C address must be a valid 7-bit device address 0x08..0x77`);
   else{const key=bus+'/'+addr;if(i2cAddress.has(key))errors.push(`${p.id}: duplicate I2C address on ${bus} with ${i2cAddress.get(key)}`);i2cAddress.set(key,p.id);}}
 }
 // Active visual GPIO ownership participates in collision detection. Multiple writes within the
 // same logical program are one owner; inactive visual editors never reserve pins.
 const activePins=new Set();
 if(project.visualMode==='flowchart'){
   const walk=steps=>{for(const n of steps||[]){if(['branch','write','setOutput'].includes(n.type))activePins.add(String(n.params.pin));walk(n.thenSteps);walk(n.elseSteps);}};
   walk(project.flowchart?.steps);
   const callsNodes=steps=>(steps||[]).some(n=>n.type==='callNodes'||callsNodes(n.thenSteps)||callsNodes(n.elseSteps));
   if(callsNodes(project.flowchart?.steps))for(const n of project.graph?.nodes||[])if(['pinMode','digitalWrite','pwmWrite','readAnalog','thresholdOutput'].includes(n.type))activePins.add(String(n.params.pin));
 }else for(const n of project.graph?.nodes||[])if(['pinMode','digitalWrite','pwmWrite','readAnalog','thresholdOutput'].includes(n.type))activePins.add(String(n.params.pin));
 for(const pin of activePins){if(!pinUsage.has(pin))continue;const logic={id:'active-logic',type:'gpio',pin,role:'program',bus:'project',shared:false};pinUsage.get(pin).push(logic);assignments.push(logic);}
 for(const [pin,usages] of pinUsage){for(let i=0;i<usages.length;i++)for(let j=i+1;j<usages.length;j++){
  const a=usages[i],b=usages[j];if(a.id===b.id&&a.role===b.role)continue;
  if(!(a.shared&&b.shared&&a.type===b.type&&a.bus===b.bus&&a.role===b.role))errors.push(`Pin ${pin} collision: ${a.id}.${a.role} and ${b.id}.${b.role}`);
 }}
 return {ok:errors.length===0,errors:[...new Set(errors)],warnings:[...new Set(warnings)],assignments,interpretation:'Shared I2C and SPI signals are permitted only on identical named buses; chip-select and incompatible roles remain exclusive; electrical validation remains external.'};
}
module.exports={plan};
