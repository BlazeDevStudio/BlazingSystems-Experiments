'use strict';
const {generateSketch,verifyProject}=require('./project.cjs');
const {profile}=require('./board.cjs');
const finite=(n,min=0,max=Number.MAX_SAFE_INTEGER)=>typeof n==='number'&&Number.isFinite(n)&&n>=min&&n<=max;
const PROVENANCE={
 'arduino:avr:uno':{flashBytes:32256,ramBytes:2048,notes:'Arduino Uno Rev3 ATmega328P: 32 KB flash (approx. 0.5 KB bootloader reserved), 2 KB SRAM; official Arduino Uno technical specifications'}
};
function parseCompilerMemory(output=''){
 const flash=/(?:Sketch uses|Program storage used:)\s*([\d,]+)\s*bytes/i.exec(output);
 const ram=/(?:Global variables use|Data memory used:)\s*([\d,]+)\s*bytes/i.exec(output);
 const flashMax=/Maximum is\s*([\d,]+)\s*bytes/i.exec(output);
 const afterRam=ram?output.slice(ram.index):'';const ramMax=/Maximum is\s*([\d,]+)\s*bytes/i.exec(afterRam);
 const parse=m=>m?Number(m[1].replace(/,/g,'')):null;
 return {flashBytes:parse(flash),ramBytes:parse(ram),flashLimitBytes:parse(flashMax),ramLimitBytes:parse(ramMax),source:'Arduino CLI compiler stdout',verifiedByCompile:!!(flash&&ram)};
}
function forecast(config){
 const {intervalSeconds=10,bytesPerRecord=48,capacityBytes=1_048_576,compressionRatio=1,retentionDays=30,format='CSV',overheadFraction=0.05}=config||{};
 if(!finite(intervalSeconds,0.001,86400)||!finite(bytesPerRecord,1,1e9)||!finite(capacityBytes,0,1e15)||!finite(compressionRatio,0.01,1)||!finite(retentionDays,0,36500)||!finite(overheadFraction,0,2))throw Error('Invalid storage forecast assumptions');
 const perRecord=bytesPerRecord*compressionRatio*(1+overheadFraction),recordsHour=3600/intervalSeconds,recordsDay=86400/intervalSeconds,dailyBytes=perRecord*recordsDay;
 const daysUntilFull=dailyBytes?capacityBytes/dailyBytes:null;
 return {type:'forecast',format,assumptions:{intervalSeconds,bytesPerRecord,capacityBytes,compressionRatio,retentionDays,overheadFraction},recordsHour,recordsDay,effectiveBytesPerRecord:perRecord,dailyBytes,sevenDaysBytes:dailyBytes*7,thirtyDaysBytes:dailyBytes*30,retentionBytes:dailyBytes*retentionDays,daysUntilFull,warning:capacityBytes>0&&daysUntilFull<retentionDays?'Projected storage will fill before configured retention; use rotation or increase verified storage capacity':null,certainty:'Estimate only; actual filesystems, sector allocation, record encoding and power-loss overhead may differ.'};
}
function analyzeResources(project,compileResult=null,logConfig=null){verifyProject(project);
 const compiled=compileResult?.ok?parseCompilerMemory([compileResult.stdout,compileResult.stderr].filter(Boolean).join('\n')):null;
 const board=PROVENANCE[project.fqbn]||null;
 const source=generateSketch(project).source;
 const observations={board:project.fqbn,firmwareMeasurement:compiled?.verifiedByCompile?compiled:null,flashCapacity:board?.flashBytes??null,ramCapacity:board?.ramBytes??null,capacitiesProvenance:board?.notes||'Unknown / Verification Required',sourceTextBytes:source?Buffer.byteLength(source,'utf8'):null,sourceIsNotBinary:true,assetBytes:null,filesystemAvailableBytes:null,psramBytes:null};
 const recommendations=[];
 if(!board)recommendations.push('Board memory limits require verified board-specific metadata. Do not assume Arduino Uno values.');
 if(!compiled?.verifiedByCompile)recommendations.push('Build with Arduino CLI to measure firmware flash/global RAM; source text length is NOT binary size.');
 if(compiled?.verifiedByCompile&&board&&compiled.ramBytes/board.ramBytes>.7)recommendations.push('Global RAM exceeds 70% of known SRAM; inspect stack/heap and large buffers.');
 if(compiled?.verifiedByCompile&&board&&compiled.flashBytes/board.flashBytes>.85)recommendations.push('Program flash usage exceeds 85%; consider reducing code/assets or selecting a compatible target.');
 if(source&&/(\bchar\s+\w+\s*\[\s*\d{4,}\s*\]|\buint8_t\s+\w+\s*\[\s*\d{4,}\s*\])/m.test(source))recommendations.push('Large static array detected by heuristic; confirm RAM/flash placement with target compiler.');
 const storage=logConfig?forecast(logConfig):null;
 if(storage?.warning)recommendations.push(storage.warning+' SD may help data storage only, not firmware executable flash or RAM.');
 return {observations,recommendations,storage,safety:'Measurements are compiler reported only; neither simulator nor forecast certifies physical hardware or real runtime memory.'};
}
module.exports={forecast,parseCompilerMemory,analyzeResources,PROVENANCE};
