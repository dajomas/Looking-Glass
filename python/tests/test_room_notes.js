const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const elements=new Map();
function element(id){
 if(!elements.has(id))elements.set(id,{value:'',checked:false,hidden:false,textContent:'',innerHTML:'',maxLength:100000,selectionStart:0,selectionEnd:0,
  classList:{values:new Set(),toggle(k,on){on?this.values.add(k):this.values.delete(k);},contains(k){return this.values.has(k);}},
  children:[],replaceChildren(){this.children=[];},appendChild(el){this.children.push(el);},
  setAttribute(k,v){this[k]=v;},focus(){},closest(){return element(id+'-label');},
  addEventListener(k,fn){this[k]=fn;},querySelectorAll(){return [];},
  setSelectionRange(s,e){this.selectionStart=s;this.selectionEnd=e;},
  setRangeText(text,s,e){this.value=this.value.slice(0,s)+text+this.value.slice(e);this.setSelectionRange(s+text.length,s+text.length);}});
 return elements.get(id);
}
let response={area_key:'a',name:'Crypt',markdown:'**Gold**',html:'<p><strong>Gold</strong></p>',revision:1,revealed:true};
let fail=false,confirmAnswer=true;
const confirmations=[];
const requests=[],store=new Map(),notices=[],context={window:{addEventListener(){}},document:{getElementById:element,querySelector:()=>element('main'),createElement:()=>({value:"",textContent:""})},
 localStorage:{getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v)},confirm:message=>{confirmations.push(message);return confirmAnswer;},navigator:{clipboard:{readText:async()=>"# Pasted"}},
 FormData:class {append(key,value){this[key]=value;}},
 LGApi:{post:async(path,body)=>{requests.push({path,body});if(fail)throw Error('save failed');if(path.endsWith('/room-note-library/import'))return {sections:2,added:2,heading_level:1,ignored_preamble:true,entries:[{id:1,name:'Imported Hall',markdown:'Gold'}]};return response;},get:async()=>({rooms:[]})}};
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
 // Imported entries are offered for empty and populated rooms as unsaved drafts.
 response={area_key:'empty',name:'',markdown:'',html:'',revision:0,revealed:true};
 await notes.select(150,100,true);
 notes.libraryEntries=[{id:1,name:'Hall',markdown:'## Treasure\nGold'},{id:2,name:'Hall',markdown:'Bones'}];notes.renderLibrary();
 assert.equal(element('room-import-choice').hidden,false);
 assert.equal(element('room-import-select').children[1].textContent,'Hall (#1)');
 element('room-import-select').value='1';const before=requests.length;element('room-import-select').onchange();
 assert.equal(requests.length,before,'choosing a library entry must not save automatically');
 assert.equal(notes.editMode,true);assert.equal(notes.dirty,true);
 assert.equal(element('room-name').value,'Hall');assert.equal(field.value,'## Treasure\nGold');
 assert.equal(element('room-import-choice').hidden,true);
 element('room-cancel').onclick();assert.equal(element('room-name').value,'');
 assert.equal(element('room-import-choice').hidden,false);
 response={...response,name:'Existing'};await notes.select(150,100,true);
 assert.equal(element('room-import-choice').hidden,false);
 element('room-import-select').value='1';const replaceBefore=requests.length;
 element('room-import-select').onchange();assert.equal(notes.editMode,true);
 assert.equal(element('room-name').value,'Hall');assert.equal(requests.length,replaceBefore);
 element('room-cancel').onclick();assert.equal(element('room-name').value,'Existing');
 element('room-edit').onclick();const clearBefore=requests.length;element('room-clear').onclick();
 assert.equal(element('room-name').value,'');assert.equal(field.value,'');assert.equal(notes.dirty,true);
 assert.equal(requests.length,clearBefore,'clear is a draft, not an immediate write');
 element('room-cancel').onclick();assert.equal(element('room-name').value,'Existing');
 assert.equal(element('room-library-import').open,false);
 element('room-library-import').open=true;notes.show(notes.room);
 assert.equal(element('room-library-import').open,true,'updates must not close a manually expanded import section');
 element('room-edit').onclick();element('room-clear').onclick();
 fail=true;await element('room-form').onsubmit({preventDefault(){}});
 assert.equal(notes.dirty,true);assert.equal(notes.editMode,true);fail=false;
 response={...response,name:'',markdown:'',html:'',revision:3};
 await element('room-form').onsubmit({preventDefault(){}});
 assert.equal(requests.at(-1).body.name,'');assert.equal(requests.at(-1).body.markdown,'');
 assert.equal(notes.editMode,false);assert.equal(notes.room.name,'');
 // Replacing notes-only saved rooms also works.
 response={...response,name:'',markdown:'Only notes',revision:4};await notes.select(150,100,true);
 assert.equal(element('room-import-choice').hidden,false);
 element('room-import-select').value='2';element('room-import-select').onchange();
 assert.equal(field.value,'Bones');element('room-cancel').onclick();assert.equal(field.value,'Only notes');
 response={...response,name:'Existing'};await notes.select(150,100,true);
 element('room-import-file').files=[{name:'rooms.md',size:50}];
 await element('room-import-form').onsubmit({preventDefault(){}});
 assert.equal(notes.libraryEntries[0].name,'Imported Hall');
 assert.ok(element('room-import-status').textContent.includes('2 new entries'));
 assert.ok(element('room-import-status').textContent.includes('ignored'));
 assert.equal(notes.room.name,'Existing','import must not replace current room');
 const importsBefore=requests.length;
 element('room-import-file').files=[{size:1048577}];
 await element('room-import-form').onsubmit({preventDefault(){}});
 assert.equal(requests.length,importsBefore,'oversize file blocked before upload');
 // Confirmation must reflect effective draft differences, not prior input events.
 response={area_key:'confirm',name:'Saved',markdown:'Notes',html:'Notes',revision:1,revealed:true};
 await notes.select(175,100,true);
 notes.libraryEntries=[{id:10,name:'Imported',markdown:'Replacement'},{id:11,name:'Saved',markdown:'Notes'}];notes.renderLibrary();
 const pick=id=>{element('room-import-select').value=String(id);element('room-import-select').onchange();};
 let count=confirmations.length;pick(10);
 assert.equal(confirmations.length,count,'saved existing content is not an unsaved draft');
 assert.equal(element('room-import-select').value,'');
 element('room-import-select').onchange();assert.equal(confirmations.length,count,'consumed actions must not replay');
 element('room-cancel').onclick();element('room-edit').onclick();
 element('room-name').value='Changed';element('room-name').oninput();
 element('room-name').value='Saved';element('room-name').oninput();assert.equal(notes.dirty,false);
 count=confirmations.length;pick(10);assert.equal(confirmations.length,count,'edit then undo needs no warning');
 element('room-cancel').onclick();element('room-edit').onclick();
 element('room-markdown').value='Unsaved';element('room-markdown').oninput();
 confirmAnswer=false;count=confirmations.length;pick(10);
 assert.equal(confirmations.length,count+1);assert.equal(field.value,'Unsaved');assert.equal(notes.dirty,true);
 element('room-import-select').onchange();assert.equal(confirmations.length,count+1,'Cancel must not re-prompt');
 confirmAnswer=true;count=confirmations.length;pick(10);assert.equal(confirmations.length,count+1);
 element('room-import-select').onchange();assert.equal(confirmations.length,count+1,'OK must not re-prompt');
 // Selecting the same content as the unsaved draft must not discard anything.
 count=confirmations.length;pick(10);assert.equal(confirmations.length,count);
 // Reentrant events during a native confirm are ignored.
 element('room-name').value='Another unsaved';element('room-name').oninput();
 context.confirm=message=>{confirmations.push(message);pick(11);return false;};
 count=confirmations.length;pick(10);assert.equal(confirmations.length,count+1);
 assert.equal(element('room-name').value,'Another unsaved');
 context.confirm=message=>{confirmations.push(message);return confirmAnswer;};
 element('room-cancel').onclick();assert.equal(notes.dirty,false);
 console.log('Room notes UI and replacement-confirmation regression tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
