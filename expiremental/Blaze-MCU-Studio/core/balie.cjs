'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
// Bounded read-only library indexing; never executes imported code or build scripts.
const MAX_FILE=512*1024, MAX_LIBRARIES=250, MAX_HEADERS=48;
const IDENT=/^[A-Za-z_]\w*$/;
function properties(text){const result={};for(const line of text.split(/\r?\n/)){const s=line.trim();if(!s||s.startsWith('#'))continue;const at=s.indexOf('=');if(at>0){const k=s.slice(0,at).trim();const v=s.slice(at+1).trim();if(IDENT.test(k))result[k]=v;}}return result;}
function readLimited(file){const s=fs.statSync(file);if(!s.isFile()||s.size>MAX_FILE)throw Error('File too large/not regular file');return fs.readFileSync(file,'utf8');}
function signatures(text){
 // Syntax-level signatures only. No preprocessor, overload or C++ semantic resolution claimed.
 const stripped=text.replace(/\/\*[\s\S]*?\*\//g,' ').replace(/\/\/[^\r\n]*/g,' ');const out=[],seen=new Set();
 const matcher=/\b([A-Za-z_]\w*(?:\s*\*)?)\s+([A-Za-z_]\w*)\s*\(([^(){};]{0,300})\)\s*(?:const\s*)?;/g;
 let m;while((m=matcher.exec(stripped))!==null){const ret=m[1].trim(),name=m[2],args=m[3].trim();if(['if','for','while','switch','return','define','typedef'].includes(name)||name.startsWith('_'))continue;
 const params=args===''||args==='void'?[]:args.split(',').map(s=>s.trim());if(params.length>10||params.some(p=>/[#{}]/.test(p)))continue;
 const token=ret+' '+name+'('+args+')';if(seen.has(token))continue;seen.add(token);
 out.push({name,returnType:ret,parameters:params,signature:token,confidence:'inferred',note:'Declaration only: conditional compilation, hardware behavior, ownership and call order are unresolved'});if(out.length>=100)break;
 }return out;
}
function listHeaders(folder){const acc=[];for(const root of [folder,path.join(folder,'src')]){if(!fs.existsSync(root))continue;for(const item of fs.readdirSync(root,{withFileTypes:true})){if(acc.length>=MAX_HEADERS)break;if(item.isFile()&&/\.(h|hpp)$/i.test(item.name))acc.push(path.join(root,item.name));}}return [...new Set(acc)];}
function inspectLibrary(folder,architecture='*'){
 const real=fs.realpathSync(folder);const metadata=path.join(real,'library.properties');if(!fs.existsSync(metadata))throw Error('Not an Arduino library: missing library.properties');
 const props=properties(readLimited(metadata));const version=props.version||'unknown';const architectures=(props.architectures||'*').split(',').map(a=>a.trim());const boardCompatible=architectures.includes('*')||architectures.includes(architecture);
 const headers=listHeaders(real),digest=crypto.createHash('sha256');digest.update(readLimited(metadata));const api=[];const warnings=[];
 for(const h of headers){try{const source=readLimited(h);digest.update(h.slice(real.length));digest.update(source);for(const signature of signatures(source)){api.push({...signature,header:path.basename(h)});}}catch(e){warnings.push(path.basename(h)+': '+e.message);}}
 if(headers.length===0)warnings.push('No top-level or src/ public headers detected');
 const unique=[...new Map(api.map(a=>[a.header+'|'+a.signature,a])).values()];
 return {name:props.name||path.basename(real),version,architectures,boardCompatible,properties:{depends:props.depends||'',includes:props.includes||'',category:props.category||'',license:props.license||''},directory:real,sourceHash:digest.digest('hex'),headers:headers.map(h=>path.basename(h)),api:unique.slice(0,150),warnings,analysis:'inferred',verifiedForBoard:false};
}
function platformLibraryRoots(dataDirectory){
 const roots=[],base=dataDirectory||process.env.ARDUINO_DIRECTORIES_DATA||(
   process.platform==='win32'?path.join(process.env.LOCALAPPDATA||path.join(os.homedir(),'AppData','Local'),'Arduino15'):
   process.platform==='darwin'?path.join(os.homedir(),'Library','Arduino15'):
   path.join(os.homedir(),'.arduino15'));
 const packages=path.join(base,'packages');if(!fs.existsSync(packages))return roots;
 for(const vendor of fs.readdirSync(packages,{withFileTypes:true})){
   if(!vendor.isDirectory()||vendor.isSymbolicLink())continue;
   const hardware=path.join(packages,vendor.name,'hardware');if(!fs.existsSync(hardware))continue;
   for(const arch of fs.readdirSync(hardware,{withFileTypes:true})){
     if(!arch.isDirectory()||arch.isSymbolicLink())continue;
     for(const version of fs.readdirSync(path.join(hardware,arch.name),{withFileTypes:true})){
       if(!version.isDirectory()||version.isSymbolicLink())continue;
       const lib=path.join(hardware,arch.name,version.name,'libraries');if(fs.existsSync(lib))roots.push(lib);
       if(roots.length>=30)return roots;
     }
   }
 }
 return roots;
}
function scanInstalled({sketchbook,architecture='*',additionalPaths=[],dataDirectory}={}){
 const roots=[];const sketch=sketchbook||path.join(os.homedir(),'Documents','Arduino');roots.push(path.join(sketch,'libraries'));
 roots.push(...platformLibraryRoots(dataDirectory));
 for(const p of additionalPaths){if(typeof p==='string'&&p.length<1024)roots.push(path.resolve(p));}
 const libraries=[],errors=[],visited=new Set();
 for(const root of roots){if(!fs.existsSync(root))continue;for(const entry of fs.readdirSync(root,{withFileTypes:true})){
  if(libraries.length>=MAX_LIBRARIES){errors.push('Library scan limit reached');break;}
  if(!entry.isDirectory()||entry.isSymbolicLink())continue;
  const folder=path.join(root,entry.name);if(!fs.existsSync(path.join(folder,'library.properties')))continue;
  try{const real=fs.realpathSync(folder);if(visited.has(real))continue;visited.add(real);libraries.push(inspectLibrary(real,architecture));}catch(e){errors.push(entry.name+': '+e.message);}
 }}
 return {libraries,errors,roots,coverage:'sketchbook and installed Arduino platform bundled libraries (bounded scan), plus optional selected directories'};
}
function libraryNodes(library){return library.api.map((f,i)=>({id:library.sourceHash.slice(0,10)+'-'+i,name:f.name,category:'Library / '+library.name,source:f.signature,header:f.header,confidence:f.confidence,boardCompatible:library.boardCompatible,codegen:'manual-adapter-required'}));}
module.exports={properties,signatures,inspectLibrary,scanInstalled,platformLibraryRoots,libraryNodes};
