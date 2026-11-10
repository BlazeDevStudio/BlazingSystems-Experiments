'use strict';
// Workspace is a directory-like relationship between independently buildable firmware targets.
// It never copies, combines, or alters a project's board core, source, or build settings.
const fs=require('node:fs');
const path=require('node:path');
const {randomUUID}=require('node:crypto');
const ID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function checkName(name){
 if(typeof name!=='string'||!name.trim()||name.trim().length>80||/[\x00-\x1F]/.test(name))throw Error('Workspace name must be 1–80 printable characters');
 return name.trim();
}
class WorkspaceCatalog {
 constructor(projectStore){
  if(!projectStore?.root||typeof projectStore.open!=='function')throw Error('Project store required');
  this.projects=projectStore;
  this.filename=path.join(projectStore.root,'_workspaces.json');
 }
 read(){
  if(!fs.existsSync(this.filename))return {version:1,items:[]};
  const data=JSON.parse(fs.readFileSync(this.filename,'utf8'));
  if(data?.version!==1||!Array.isArray(data.items)||data.items.length>100)throw Error('Invalid workspace catalog: recovery required');
  const ids=new Set();
  for(const x of data.items){
   if(!ID.test(x?.id||'')||ids.has(x.id)||checkName(x.name)!==x.name||!Array.isArray(x.projectIds)||x.projectIds.length>100||new Set(x.projectIds).size!==x.projectIds.length||x.projectIds.some(id=>!ID.test(id)))throw Error('Invalid workspace catalog entry');
   ids.add(x.id);
  }
  return data;
 }
 write(data){
  const tmp=this.filename+'.'+process.pid+'.'+randomUUID()+'.tmp';
  try{
   fs.writeFileSync(tmp,JSON.stringify(data,null,2)+'\n',{encoding:'utf8',flag:'wx'});
   fs.renameSync(tmp,this.filename);
  }finally{if(fs.existsSync(tmp))fs.rmSync(tmp);}
 }
 list(){return this.read().items.map(x=>({...x,projectIds:[...x.projectIds],missingIds:x.projectIds.filter(id=>{try{this.projects.open(id);return false;}catch{return true;}})}));}
 get(id){if(!ID.test(String(id)))throw Error('Invalid workspace ID');const workspace=this.list().find(x=>x.id===id);if(!workspace)throw Error('Workspace not found');return workspace;}
 create(name){const entry={id:randomUUID(),name:checkName(name),projectIds:[],createdAt:new Date().toISOString()};const data=this.read();if(data.items.length>=100)throw Error('Workspace limit reached');data.items.push(entry);this.write(data);return structuredClone(entry);}
 rename(id,name){return this.edit(id,x=>{x.name=checkName(name);});}
 add(id,projectId){if(!ID.test(String(projectId)))throw Error('Invalid project ID');this.projects.open(projectId);return this.edit(id,x=>{if(!x.projectIds.includes(projectId)){if(x.projectIds.length>=100)throw Error('Workspace project limit reached');x.projectIds.push(projectId);}});}
 remove(id,projectId){if(!ID.test(String(projectId)))throw Error('Invalid project ID');return this.edit(id,x=>{x.projectIds=x.projectIds.filter(p=>p!==projectId);});}
 delete(id){if(!ID.test(String(id)))throw Error('Invalid workspace ID');const data=this.read();const n=data.items.findIndex(x=>x.id===id);if(n<0)throw Error('Workspace not found');const [old]=data.items.splice(n,1);this.write(data);return {id:old.id,removedAssociationCount:old.projectIds.length,projectsDeleted:0};}
 edit(id,change){if(!ID.test(String(id)))throw Error('Invalid workspace ID');const data=this.read();const x=data.items.find(w=>w.id===id);if(!x)throw Error('Workspace not found');change(x);this.write(data);return {...x,projectIds:[...x.projectIds]};}
}
module.exports={WorkspaceCatalog,checkName};
