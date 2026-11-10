'use strict';
// Desktop session layout is separate from the independent firmware projects.
// Restore never writes project source or resurrects deleted project directories.
const fs=require('node:fs');
const path=require('node:path');
const {randomUUID}=require('node:crypto');
const ID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const empty=()=>({version:1,workspaceId:'',openProjectIds:[],activeProjectId:null});
function validate(value){
 if(!value||typeof value!=='object'||Array.isArray(value)||value.version!==1
  ||typeof value.workspaceId!=='string'||(value.workspaceId!==''&&!ID.test(value.workspaceId))
  ||!Array.isArray(value.openProjectIds)||value.openProjectIds.length>32
  ||value.openProjectIds.some(id=>typeof id!=='string'||!ID.test(id))
  ||new Set(value.openProjectIds).size!==value.openProjectIds.length
  ||(value.activeProjectId!==null&&(!ID.test(String(value.activeProjectId))||!value.openProjectIds.includes(value.activeProjectId))))
  throw Error('Invalid desktop session layout: recovery required');
 return {version:1,workspaceId:value.workspaceId,openProjectIds:[...value.openProjectIds],activeProjectId:value.activeProjectId};
}
class DesktopSession {
 constructor(projectStore,workspaceCatalog){
  if(!projectStore?.root||typeof projectStore.open!=='function'||typeof workspaceCatalog?.list!=='function')
   throw Error('Project store and workspace catalog required');
  this.projects=projectStore;this.workspaces=workspaceCatalog;
  this.filename=path.join(projectStore.root,'_desktop_session.json');
 }
 read(){return fs.existsSync(this.filename)?validate(JSON.parse(fs.readFileSync(this.filename,'utf8'))):empty();}
 reconcile(value){
  const state=validate(value);
  const available=state.openProjectIds.filter(id=>{try{this.projects.open(id);return true;}catch{return false;}});
  // A deleted workspace is only a filter: never drop otherwise valid firmware tabs.
  const workspaceId=state.workspaceId&&this.workspaces.list().some(w=>w.id===state.workspaceId)?state.workspaceId:'';
  return {version:1,workspaceId,openProjectIds:available,
   activeProjectId:available.includes(state.activeProjectId)?state.activeProjectId:(available.at(-1)||null)};
 }
 load(){return this.reconcile(this.read());}
 save(state){
  const normalized=this.reconcile({...state,version:1});
  const tmp=this.filename+'.'+process.pid+'.'+randomUUID()+'.tmp';
  try{
   fs.writeFileSync(tmp,JSON.stringify(normalized,null,2)+'\n',{encoding:'utf8',flag:'wx'});
   fs.renameSync(tmp,this.filename);
  }finally{if(fs.existsSync(tmp))fs.rmSync(tmp);}
  return normalized;
 }
}
module.exports={DesktopSession,validate};
