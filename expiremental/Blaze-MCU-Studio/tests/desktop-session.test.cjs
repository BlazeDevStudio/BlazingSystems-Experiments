'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {WorkspaceStore}=require('../core/storage.cjs');
const {WorkspaceCatalog}=require('../core/workspaces.cjs');
const {DesktopSession}=require('../core/desktop-session.cjs');
function fixture(fn){const root=fs.mkdtempSync(path.join(os.tmpdir(),'blaze-session-'));
 try{const ps=new WorkspaceStore(root),ws=new WorkspaceCatalog(ps);return fn(ps,ws,new DesktopSession(ps,ws),root);}
 finally{fs.rmSync(root,{recursive:true,force:true});}}
test('desktop session persists Uno and ESP tabs, active target, workspace selection without firmware mutation',()=>fixture((ps,ws,session,root)=>{
 const a=ps.create('Uno','arduino:avr:uno'),b=ps.create('ESP','esp32:esp32:esp32'),w=ws.create('Lab');
 ws.add(w.id,a.id);ws.add(w.id,b.id);
 const beforeA=fs.readFileSync(ps.filename(a.id),'utf8'),beforeB=fs.readFileSync(ps.filename(b.id),'utf8');
 const expected={version:1,workspaceId:w.id,openProjectIds:[a.id,b.id],activeProjectId:a.id};
 assert.deepEqual(session.save(expected),expected);
 assert.deepEqual(new DesktopSession(new WorkspaceStore(root),new WorkspaceCatalog(new WorkspaceStore(root))).load(),expected);
 assert.equal(fs.readFileSync(ps.filename(a.id),'utf8'),beforeA);
 assert.equal(fs.readFileSync(ps.filename(b.id),'utf8'),beforeB);
}));
test('closing a tab persists new layout; trashed targets and removed collections are filtered on next startup',()=>fixture((ps,ws,session)=>{
 const a=ps.create('A'),b=ps.create('B'),w=ws.create('Workspace');
 session.save({workspaceId:w.id,openProjectIds:[a.id,b.id],activeProjectId:b.id});
 session.save({workspaceId:w.id,openProjectIds:[a.id],activeProjectId:a.id});
 assert.deepEqual(session.load().openProjectIds,[a.id]);
 session.save({workspaceId:w.id,openProjectIds:[a.id,b.id],activeProjectId:b.id});
 ps.trash(b.id);ws.delete(w.id);
 assert.deepEqual(session.load(),{version:1,workspaceId:'',openProjectIds:[a.id],activeProjectId:a.id});
 assert.equal(ps.open(a.id).name,'A');assert.equal(ps.recoveryList()[0].id,b.id);
}));
test('invalid session fields and malicious paths fail closed without modifying projects',()=>fixture((ps,ws,session,root)=>{
 const a=ps.create('Safe');
 assert.throws(()=>session.save({workspaceId:'../../etc',openProjectIds:[a.id],activeProjectId:a.id}),/Invalid desktop session/);
 assert.throws(()=>session.save({workspaceId:'',openProjectIds:[a.id,a.id],activeProjectId:a.id}),/Invalid desktop session/);
 assert.throws(()=>session.save({workspaceId:'',openProjectIds:['../../escape'],activeProjectId:null}),/Invalid desktop session/);
 assert.throws(()=>session.save({workspaceId:'',openProjectIds:[a.id],activeProjectId:'00000000-0000-0000-0000-000000000000'}),/Invalid desktop session/);
 fs.writeFileSync(path.join(root,'_desktop_session.json'),'{broken JSON');
 assert.throws(()=>session.load(),SyntaxError);
 assert.equal(ps.open(a.id).name,'Safe');
}));
test('missing session starts with empty layout; valid missing targets are ignored, never re-created',()=>fixture((ps,ws,session)=>{
 assert.deepEqual(session.load(),{version:1,workspaceId:'',openProjectIds:[],activeProjectId:null});
 const a=ps.create('Live');
 const ghost='11111111-1111-4111-8111-111111111111';
 const r=session.save({workspaceId:'',openProjectIds:[ghost,a.id],activeProjectId:ghost});
 assert.deepEqual(r.openProjectIds,[a.id]);assert.equal(r.activeProjectId,a.id);
 assert.equal(fs.existsSync(ps.folder(ghost)),false);
}));
