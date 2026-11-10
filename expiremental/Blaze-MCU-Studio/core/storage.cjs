'use strict';
const fs=require('node:fs'); const path=require('node:path'); const {randomUUID}=require('node:crypto');
const {createProject,verifyProject,generateSketch,sketchName}=require('./project.cjs');
const ID_RE=/^[0-9a-f-]{36}$/i;
class WorkspaceStore {
  constructor(root){ this.root=path.resolve(root); fs.mkdirSync(this.root,{recursive:true}); }
  folder(id){ if(!ID_RE.test(id)) throw new Error('Invalid project id'); return path.join(this.root,id); }
  filename(id){ return path.join(this.folder(id),'project.blaze.json'); }
  list(){return fs.readdirSync(this.root,{withFileTypes:true}).filter(x=>x.isDirectory()&&ID_RE.test(x.name)).flatMap(x=>{try { const p=this.open(x.name);return [{id:p.id,name:p.name,fqbn:p.fqbn,updatedAt:p.updatedAt}]; }catch{return [];}}).sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt)); }
  create(name,fqbn,template='blink'){const p=createProject(name,fqbn,template);this.save(p);return p;}
  open(id){const p=JSON.parse(fs.readFileSync(this.filename(id),'utf8'));verifyProject(p);if(p.id!==id)throw Error('Project id mismatch');return p;}
  save(p){ verifyProject(p);const dir=this.folder(p.id), filename=this.filename(p.id);fs.mkdirSync(dir,{recursive:true});if(fs.existsSync(filename)) {const current=this.open(p.id);if(current.id!==p.id)throw Error('Project mismatch');const backups=path.join(dir,'history');fs.mkdirSync(backups,{recursive:true}); const key=Date.now().toString()+'-'+Math.floor(Math.random()*100000).toString();fs.copyFileSync(filename,path.join(backups,key+'.json'));const files=fs.readdirSync(backups).sort();for(const old of files.slice(0,-5)) fs.rmSync(path.join(backups,old));}
    p.updatedAt=new Date().toISOString(); const temporary=path.join(dir,'.project-'+process.pid+'-'+Date.now()+'.tmp'); try{fs.writeFileSync(temporary,JSON.stringify(p,null,2)+'\n',{encoding:'utf8',flag:'wx'});fs.renameSync(temporary,filename);} finally {if(fs.existsSync(temporary))fs.rmSync(temporary);};return p; }
  rename(id,name){const p=this.open(id);if(typeof name!=='string'||!name.trim()||name.length>80)throw Error('Invalid project name');p.name=name.trim();return this.save(p);}
  duplicate(id){const original=this.open(id);const p=structuredClone(original);p.id=randomUUID();p.name=original.name+' Copy';p.createdAt=new Date().toISOString();return this.save(p);}
  trash(id){const p=this.open(id);const trashFolder=path.join(this.root,'_recovery');fs.mkdirSync(trashFolder,{recursive:true});const destination=path.join(trashFolder,id);if(fs.existsSync(destination))throw Error('Recovery folder already contains this project');fs.renameSync(this.folder(id),destination);return {id:p.id,name:p.name,recoverable:true};}
  recover(id){const source=path.join(this.root,'_recovery',id);if(!ID_RE.test(id)||!fs.existsSync(source)||fs.existsSync(this.folder(id)))throw Error('Recovery unavailable');fs.renameSync(source,this.folder(id));return this.open(id);}
  recoveryList(){const dir=path.join(this.root,'_recovery');if(!fs.existsSync(dir))return [];return fs.readdirSync(dir,{withFileTypes:true}).filter(x=>x.isDirectory()&&ID_RE.test(x.name)).map(x=>({id:x.name}));}
  export(p,target){ verifyProject(p);const result=generateSketch(p);if(!result.source || !result.source.trim())throw Error('No valid sketch to export: '+result.diagnostics.errors.join('; ')); const parent=path.resolve(target);fs.mkdirSync(parent,{recursive:true});const dir=path.join(parent,sketchName(p.name));if(fs.existsSync(dir))throw Error('Export refused: target sketch folder already exists. Choose an empty destination to avoid overwriting user files.');fs.mkdirSync(dir);const filename=path.join(dir,sketchName(p.name)+'.ino');fs.writeFileSync(filename,result.source,'utf8');fs.writeFileSync(path.join(dir,'blaze-project.json'),JSON.stringify({schemaVersion:p.schemaVersion,fqbn:p.fqbn,libraryDependencies:[...new Set([...(p.libraryDependencies||[]),...(result.dependencies||[])])],sourceMode:p.source.mode,exportedAt:new Date().toISOString()},null,2));return {filename,folder:dir}; }
}
module.exports={WorkspaceStore};
