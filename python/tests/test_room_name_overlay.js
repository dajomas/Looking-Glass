const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const nodes={};function node(id){return nodes[id]||={hidden:true,checked:false,textContent:'',attrs:{},events:{},
 setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this[k];},addEventListener(k,fn){this.events[k]=fn;}};}
const pending=[],errors=[];
const c={window:{},document:{getElementById:node},LGApi:{get:path=>new Promise((resolve,reject)=>pending.push({path,resolve,reject}))}};
vm.runInNewContext(fs.readFileSync('static/js/room_name_overlay.js','utf8'),c);
(async()=>{
 const overlay=new c.window.LGRoomNameOverlay(1,message=>errors.push(message));
 assert.equal(node('room-name-toggle').hidden,true);
 node('room-select-mode').checked=true;node('room-select-mode').events.change();
 assert.equal(node('room-name-toggle').hidden,false);assert.equal(pending.length,0);
 node('room-name-toggle').onclick();assert.equal(pending.length,1);assert.equal(node('room-name-toggle').attrs['aria-pressed'],'true');
 pending[0].resolve({png:'colors',named:2,unnamed:3});await new Promise(setImmediate);
 assert.equal(node('room-name-overlay').hidden,false);assert.ok(node('room-name-legend').textContent.includes('named (2)'));
 node('room-name-toggle').onclick();assert.equal(node('room-name-overlay').hidden,true);
 node('room-name-toggle').onclick();assert.equal(pending.length,2);
 node('room-select-mode').checked=false;node('room-select-mode').events.change();
 pending[1].resolve({png:'late',named:2,unnamed:3});await new Promise(setImmediate);
 assert.equal(node('room-name-overlay').hidden,true);assert.equal(node('room-name-toggle').hidden,true);
 node('room-select-mode').checked=true;node('room-select-mode').events.change();
 assert.equal(overlay.enabled,false,'unchecking must reset, not silently re-enable, coverage');
 node('room-name-toggle').onclick();pending[2].resolve({png:'new',named:1,unnamed:4});await new Promise(setImmediate);
 overlay.mapChanged({cache_token:'t',walls_version:1,width:400,height:200});assert.equal(pending.length,4);
 pending[3].reject(Error('failed'));await new Promise(setImmediate);assert.equal(errors.length,1);assert.equal(node('room-name-overlay').hidden,true);
 console.log('Name coverage toggle, counts, disabling, invalidation and late-response tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
