const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const elements={};function el(id){return elements[id]||=( {hidden:true,textContent:'',src:'',removeAttribute(k){delete this[k];}});}
const pending=[],errors=[];
const c={window:{},document:{getElementById:el},LGApi:{post:(path,body)=>new Promise((resolve,reject)=>pending.push({path,body,resolve,reject}))}};
vm.runInNewContext(fs.readFileSync('static/js/room_edit_marker.js','utf8'),c);
(async()=>{
 const marker=new c.window.LGRoomEditMarker(1,message=>errors.push(message));
 const room={area_key:'a',name:'Crypt'},point={x:100,y:100};
 marker.set(true,room,point);assert.equal(pending.length,1);assert.equal(el('room-edit-indicator').hidden,false);
 marker.set(false,room,point);pending[0].resolve({area_key:'a',png:'late'});await new Promise(setImmediate);
 assert.equal(el('room-edit-overlay').hidden,true,'late response must not resurrect cancelled editing');
 marker.set(true,room,point);pending[1].resolve({area_key:'a',png:'mask'});await new Promise(setImmediate);
 assert.equal(el('room-edit-overlay').src,'data:image/png;base64,mask');assert.equal(el('room-edit-overlay').hidden,false);
 marker.set(true,room,point);assert.equal(pending.length,2,'same target does not refetch');
 marker.mapChanged({cache_token:'t',walls_version:1,width:400,height:200});
 marker.mapChanged({cache_token:'t',walls_version:2,width:400,height:200});assert.equal(pending.length,3);
 pending[2].reject(Error('Room geometry changed'));await new Promise(setImmediate);assert.equal(el('room-edit-overlay').hidden,true);assert.equal(errors.length,1);
 marker.set(false,null,null);assert.equal(el('room-edit-indicator').hidden,true);
 console.log('Edit overlay lifecycle, geometry invalidation and stale-response tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
