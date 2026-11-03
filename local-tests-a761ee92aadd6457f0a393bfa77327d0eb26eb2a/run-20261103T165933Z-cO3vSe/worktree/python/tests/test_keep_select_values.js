const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const tasks=[],storage=new Map(),capture=[];
let observer;
class Select {
 constructor(id){this.id=id;this.name='';this.value='';this.disabled=false;this.options=[{value:''},{value:'1'}];this.events=0;}
 closest(){return null;}
 dispatchEvent(event){event.target=this;for(const fn of capture)fn(event);this.events++;if(this.id==='room-import-select'){this.value='';observer();}}
}
const action=new Select('room-import-select'),normal=new Select('saved-source');
const path='/maps/7',actionKey=`lg:select:${path}:room-import-select:`,normalKey=`lg:select:${path}:saved-source:`;
storage.set(actionKey,'1');storage.set(normalKey,'1');
const context={location:{pathname:path},HTMLSelectElement:Select,
 localStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)},
 document:{body:{},addEventListener:(type,fn)=>capture.push(fn),querySelectorAll:()=>[action,normal]},
 Event:class{constructor(type,opts){this.type=type;}},queueMicrotask:fn=>tasks.push(fn),
 MutationObserver:class{constructor(fn){observer=fn;}observe(){}}};
vm.runInNewContext(fs.readFileSync('static/js/keep_select_values.js','utf8'),context);
let steps=0;while(tasks.length&&steps++<10)tasks.shift()();
assert.equal(action.events,0,'stored room-import selection must never dispatch a synthetic change');
assert.equal(action.value,'');assert.equal(normal.value,'1');assert.equal(normal.events,1,'ordinary dropdown restoration must still work');
assert.equal(tasks.length,0,'restoring dropdowns must not create an action feedback loop');
storage.delete(actionKey);action.value='1';action.dispatchEvent(new context.Event('change'));
assert.equal(storage.has(actionKey),false,'new import selections must not be persisted');
console.log('One-shot action exclusion and ordinary select restoration tests passed');
