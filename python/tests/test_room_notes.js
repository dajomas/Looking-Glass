const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{value:'',checked:false,hidden:false,textContent:'',innerHTML:'',classList:{values:new Set(),toggle(k,on){on?this.values.add(k):this.values.delete(k);},contains(k){return this.values.has(k);}},setAttribute(k,v){this[k]=v;}});return elements.get(id);}
let response={area_key:'a',name:'Crypt',markdown:'**Gold**',html:'<p><strong>Gold</strong></p>',revision:1,revealed:true};
const requests=[],store=new Map(),context={window:{addEventListener(){}},document:{getElementById:element,querySelector:()=>element('main')},
 localStorage:{getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v)},confirm:()=>true,
 LGApi:{post:async(path,body)=>{requests.push({path,body});return response;},get:async()=>({rooms:[]})}};
vm.runInNewContext(fs.readFileSync('static/js/room_notes.js','utf8'),context);
(async()=>{
 const notes=new context.window.LGRoomNotes(1,()=>{});
 await notes.select(100,100,true);
 assert.equal(element('room-title').textContent,'Crypt');assert.equal(element('room-preview').innerHTML,response.html);
 assert.equal(element('room-form').hidden,false);
 notes.collapse(true);assert.equal(element('room-panel-body').hidden,true);assert.equal(element('room-toggle')['aria-expanded'],'false');
 await notes.select(100,100);assert.equal(element('room-panel-body').hidden,true,'selection must respect deliberate collapse');
 element('room-name').value='Renamed';element('room-name').oninput();assert.equal(notes.dirty,true);
 response={...response,name:'Renamed',revision:2};
 await element('room-form').onsubmit({preventDefault(){},submitter:{disabled:false}});
 assert.equal(notes.dirty,false);assert.equal(requests.at(-1).body.revision,1);
 response={...response,revealed:false};await notes.select(100,100);
 assert.equal(element('room-preview').innerHTML,'<p><strong>Gold</strong></p>');
 assert.equal(element('room-preview').textContent,'');assert.equal(element('room-form').hidden,true);
 console.log('Room notes UI tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
