const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const elements=new Map();
function element(id){
 if(!elements.has(id))elements.set(id,{value:'',checked:false,hidden:false,textContent:'',innerHTML:'',maxLength:100000,selectionStart:0,selectionEnd:0,
  classList:{values:new Set(),toggle(k,on){on?this.values.add(k):this.values.delete(k);},contains(k){return this.values.has(k);}},
  setAttribute(k,v){this[k]=v;},focus(){},closest(){return element(id+'-label');},
  addEventListener(k,fn){this[k]=fn;},querySelectorAll(){return [];},
  setSelectionRange(s,e){this.selectionStart=s;this.selectionEnd=e;},
  setRangeText(text,s,e){this.value=this.value.slice(0,s)+text+this.value.slice(e);this.setSelectionRange(s+text.length,s+text.length);}});
 return elements.get(id);
}
let response={area_key:'a',name:'Crypt',markdown:'**Gold**',html:'<p><strong>Gold</strong></p>',revision:1,revealed:true};
let fail=false,confirmAnswer=true;
const requests=[],store=new Map(),notices=[],context={window:{addEventListener(){}},document:{getElementById:element,querySelector:()=>element('main')},
 localStorage:{getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v)},confirm:()=>confirmAnswer,navigator:{clipboard:{readText:async()=>"# Pasted"}},
 LGApi:{post:async(path,body)=>{requests.push({path,body});if(fail)throw Error('save failed');return response;},get:async()=>({rooms:[]})}};
vm.runInNewContext(fs.readFileSync('static/js/room_notes.js','utf8'),context);
(async()=>{
 const notes=new context.window.LGRoomNotes(1,(...args)=>notices.push(args));
 await notes.select(100,100,true);
 assert.equal(element('room-title').textContent,'Crypt');
 assert.equal(element('room-form').hidden,true);assert.equal(element('room-read').hidden,false);
 element('room-edit').onclick();assert.equal(notes.editMode,true);
 assert.equal(element('room-form').hidden,false);assert.equal(element('room-read').hidden,true);
 const field=element('room-markdown');
 function draft(value,s=0,e=value.length){field.value=value;field.setSelectionRange(s,e);}
 draft('gold');notes.format('bold');assert.equal(field.value,'**gold**');assert.equal(notes.dirty,true);
 draft('gold');notes.format('italic');assert.equal(field.value,'*gold*');
 draft('gold');notes.format('strike');assert.equal(field.value,'~~gold~~');
 draft('gold');notes.format('code');assert.equal(field.value,'`gold`');
 draft('gold');notes.format('link');assert.equal(field.value,'[gold](https://example.com)');
 draft('one\ntwo');notes.format('number');assert.equal(field.value,'1. one\n2. two');
 draft('one\ntwo');notes.format('bullet');assert.equal(field.value,'- one\n- two');
 draft('one');notes.format('heading');assert.equal(field.value,'## one');
 draft('one');notes.format('quote');assert.equal(field.value,'> one');
 draft('```');notes.format('fence');assert.equal(field.value,'````\n```\n````\n');
 draft('',0,0);notes.format('rule');assert.ok(field.value.includes('---'));
 draft('abc',1,2);let prevented=false;
 field.paste({clipboardData:{types:['text/plain','text/markdown'],getData:m=>m==='text/markdown'?'**MD**':'plain'},preventDefault(){prevented=true;}});
 assert.equal(prevented,true);assert.equal(field.value,'a**MD**c');
 draft('',0,0);await element('room-paste').onclick();assert.equal(field.value,'# Pasted');
 context.navigator.clipboard.readText=async()=>{throw Error('denied');};await element('room-paste').onclick();assert.ok(notices.at(-1)[0].includes('Ctrl+V'));
 draft('x'.repeat(100000),100000,100000);notes.insert('y');assert.equal(field.value.length,100000);
 confirmAnswer=false;await notes.select(200,100,true);assert.equal(notes.point.x,100);confirmAnswer=true;
 element('room-cancel').onclick();assert.equal(notes.editMode,false);assert.equal(field.value,'**Gold**');assert.equal(notes.dirty,false);
 element('room-edit').onclick();element('room-name').value='Renamed';element('room-name').oninput();
 fail=true;await element('room-form').onsubmit({preventDefault(){}});assert.equal(notes.editMode,true);assert.equal(notes.dirty,true);fail=false;
 response={...response,name:'Renamed',revision:2};await element('room-form').onsubmit({preventDefault(){}});
 assert.equal(notes.editMode,false);assert.equal(notes.dirty,false);assert.equal(element('room-title').textContent,'Renamed');assert.equal(requests.at(-1).body.revision,1);
 notes.collapse(true);await notes.select(100,100);assert.equal(element('room-panel-body').hidden,true);
 response={...response,revealed:false};await notes.select(100,100);assert.equal(element('room-read').hidden,true);assert.equal(element('room-form').hidden,true);
 console.log('Room notes read/edit, toolbar, paste, validation and save regression tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
