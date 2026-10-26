'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {parseBoardCatalog,combineBoards,CORE_URLS,STARTER_TARGETS}=require('../core/arduino.cjs');
test('fresh install catalog includes ESP8266 and ESP32 with honest uninstalled status',()=>{
 const result=combineBoards([]);
 for(const name of ['esp8266:esp8266:generic','esp32:esp32:esp32','arduino:avr:uno']){
  const board=result.find(x=>x.fqbn===name);assert(board);assert.equal(board.installed,false);assert.match(board.status,/install/i);
 }
});
test('boards discovered through CLI installed platform override starter entries',()=>{
 const installed=parseBoardCatalog(JSON.stringify({boards:[{name:'UNO R3',fqbn:'arduino:avr:uno'},{name:'Custom board',fqbn:'vendor:custom:board1'}]}));
 const all=combineBoards(installed);assert.equal(all.filter(b=>b.fqbn==='arduino:avr:uno').length,1);
 assert.equal(all.find(b=>b.fqbn==='arduino:avr:uno').name,'UNO R3');
 assert.equal(all.find(b=>b.fqbn==='vendor:custom:board1').installed,true);
 assert.equal(all.find(b=>b.fqbn==='esp32:esp32:esp32').installed,false);
});
test('unrecognized CLI FQBN entries are not shown as installed',()=>{
 const a=parseBoardCatalog(JSON.stringify({boards:[{name:'Malformed',fqbn:'esp8266'},{name:'Valid',fqbn:'esp8266:esp8266:generic'}]}));
 assert.equal(a.length,1);
});
test('third-party starter core URLs come from known project upstream, no auto download',()=>{
 assert.match(CORE_URLS['esp8266:esp8266'],/^https:\/\/arduino\.esp8266\.com\//);
 assert.match(CORE_URLS['esp32:esp32'],/^https:\/\/espressif\.github\.io\//);
 assert(STARTER_TARGETS.length>=5);
});
