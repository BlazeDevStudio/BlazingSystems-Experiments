'use strict';
const RE=/^[\w.-]+:[\w.-]+:[\w.-]+(?::[\w.,=~-]+)?$/;
const PROFILES={
 'arduino:avr:uno':{provenance:'Arduino Uno Rev3 official pinout; partial digital pin model',verified:true,pins:Array.from({length:14},(_,i)=>String(i)),reserved:['0','1'],capabilities:{digital:true,adc:'A0–A5 not yet modeled',pwm:'board-specific verification required'}}
};
function profile(fqbn){return PROFILES[fqbn]||null;}
function analyzeBoardChange(project,target){if(!RE.test(target))throw Error('Invalid target FQBN');const before=profile(project.fqbn),after=profile(target),issues=[],warnings=[];
 const active=(project.graph?.nodes||[]).filter(n=>['pinMode','digitalWrite'].includes(n.type)).map(n=>({id:n.id,pin:String(n.params.pin)}));
 const visit=list=>{for(const n of list||[]){if(['setOutput','write','branch'].includes(n.type))active.push({id:n.id,pin:String(n.params.pin)});visit(n.thenSteps);visit(n.elseSteps);}};visit(project.flowchart?.steps);
 for(const pin of active){if(after&&!after.pins.includes(pin.pin))issues.push(pin.id+': D'+pin.pin+' unavailable on '+target);else if(!after)warnings.push(pin.id+': pin '+pin.pin+' not verified for '+target);}
 if(project.libraryDependencies?.length)warnings.push('Library compatibility needs re-analysis for new architecture');
 return {from:project.fqbn,to:target,compatible:issues.length===0&&warnings.length===0,issues,warnings,oldProfile:before?.provenance||'Unknown',newProfile:after?.provenance||'Unknown / Verification Required',requiresSnapshot:true};
}
module.exports={RE,PROFILES,profile,analyzeBoardChange};
