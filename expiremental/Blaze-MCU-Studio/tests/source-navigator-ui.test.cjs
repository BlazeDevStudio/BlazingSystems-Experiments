
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..');
test('generated-code navigator exists and is wired to visual nodes, flowcharts and source caret',()=>{
 const html=fs.readFileSync(path.join(root,'renderer/index.html'),'utf8'),app=fs.readFileSync(path.join(root,'renderer/app.js'),'utf8');
 for(const id of ['codeMapList','codeMapStatus','codeEditor'])assert(html.includes(`id="${id}"`),id);
 for(const token of ['function renderSourceMap(','data-map-line','data-map-block','function locateVisualBlock(','data-view-source','data-flow-source','sourceRowStatus'])assert(app.includes(token),token);
});
