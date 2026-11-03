// Editor-only contracts using the real class with isolated DOM/API doubles.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('static/js/room_notes.js','utf8');
const plain=value=>JSON.parse(JSON.stringify(value));
const initial={area_key:'a'.repeat(64),cache_token:'selected-map',walls_version:7,room_notes_version:3,revision:2,
  name:'Crypt',markdown:'Original',html:'<p>Original</p>',revealed:true};
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};}
async function fixture(){
  const elements=new Map(),handlers=new Map(),requests=[],notices=[];
  function element(id){
    if(!elements.has(id)){
      const classes=new Set();
      elements.set(id,{value:'',checked:false,hidden:false,disabled:false,textContent:'',innerHTML:'',children:[],
        classList:{toggle(k,on){on?classes.add(k):classes.delete(k);},contains(k){return classes.has(k);}},
        replaceChildren(){this.children=[];},appendChild(child){this.children.push(child);},
        setAttribute(k,v){this[k]=v;},removeAttribute(k){delete this[k];},focus(){},
        closest(){return element(id+'-label');},addEventListener(k,fn){this[k]=fn;},
        querySelectorAll(){return ['room-name','room-markdown','room-save','room-cancel'].map(element);}});
    }
    return elements.get(id);
  }
  const api={post:async()=>({...initial}),get:async()=>({entries:[],rooms:[]})};
  const context={window:{addEventListener(k,fn){handlers.set(k,fn);}},
    document:{getElementById:element,querySelector:()=>element('main'),createElement:()=>({value:'',textContent:''})},
    localStorage:{getItem(){return null;},setItem(){}},confirm:()=>true,navigator:{},
    FormData:class {append(){}},LGApi:{
      post(path,body){requests.push({path,body:plain(body)});return api.post(path,body);},
      get(path){return api.get(path);}}};
  vm.runInNewContext(source,context);
  const notes=new context.window.LGRoomNotes(1,(...args)=>notices.push(args));
  notes.point={x:100,y:50};notes.show({...initial});notes.setEditMode(true);
  await notes.loadLibrary();
  const edit=(name,markdown)=>{element('room-name').value=name;element('room-name').oninput();
    element('room-markdown').value=markdown;element('room-markdown').oninput();};
  const submit=()=>element('room-form').onsubmit({preventDefault(){}});
  return {notes,api,element,handlers,requests,notices,edit,submit};
}
const cases=[];
function test(name,run){cases.push({name,run});}

test('save uses selected context, not newer background stamps, and installs returned context',async()=>{
  const h=await fixture();
  h.edit('Edited','Draft\r\n🐉');
  await h.notes.refresh({cache_token:'newer-background',walls_version:99,fog_version:99});
  h.api.post=async()=>({...initial,name:'Edited',markdown:'Draft\r\n🐉',revision:3,room_notes_version:4});
  await h.submit();
  assert.equal(h.requests.length,1);
  assert.deepEqual(h.requests[0],{path:'/api/maps/1/room-notes',body:{x:100,y:50,
    area_key:initial.area_key,revision:2,cache_token:'selected-map',walls_version:7,room_notes_version:3,
    name:'Edited',markdown:'Draft\r\n🐉'}});
  assert.equal(h.notes.room.revision,3);assert.equal(h.notes.room.room_notes_version,4);
  assert.equal(h.notes.editMode,false);assert.equal(h.notes.dirty,false);assert.equal(h.notes.saving,false);
  assert.equal(h.element('room-name').disabled,false);
});

test('rejection retains draft and context, releases controls and never automatically retries',async()=>{
  const h=await fixture(),selected=h.notes.room;
  h.edit('Unsaved','Keep this\r\n🐉');
  h.api.post=async()=>{throw Error('Room geometry or notes changed');};
  await h.submit();
  assert.equal(h.requests.length,1);assert.equal(h.notes.room,selected);
  assert.equal(h.element('room-name').value,'Unsaved');assert.equal(h.element('room-markdown').value,'Keep this\r\n🐉');
  assert.equal(h.notes.editMode,true);assert.equal(h.notes.dirty,true);assert.equal(h.notes.saving,false);
  assert.equal(h.element('room-name').disabled,false);assert.equal(h.element('room-cancel').disabled,false);
  assert.equal(h.notes.room.room_notes_version,3);assert.equal(h.notices.at(-1)[1],'error');
  let prevented=false;const event={preventDefault(){prevented=true;}};h.handlers.get('beforeunload')(event);
  assert.equal(prevented,true);assert.equal(event.returnValue,'');
});

test('a delayed selection cannot overwrite editing begun after the request',async()=>{
  const h=await fixture(),pending=deferred(),selected=h.notes.room;
  h.api.post=()=>pending.promise;
  const selecting=h.notes.select(230,50,true);
  h.edit('Local draft','Do not replace');
  pending.resolve({...initial,name:'Delayed room',cache_token:'stale-response'});
  await selecting;
  assert.equal(h.notes.room,selected);assert.equal(h.notes.point.x,100);
  assert.equal(h.element('room-name').value,'Local draft');assert.equal(h.element('room-markdown').value,'Do not replace');
  assert.equal(h.notes.dirty,true);
});

test('saving invalidates pending selection, blocks duplicate submission and installs only save result',async()=>{
  const h=await fixture(),selection=deferred(),saving=deferred(),selected=h.notes.room;
  h.api.post=path=>path.endsWith('/room-at')?selection.promise:saving.promise;
  const selecting=h.notes.select(230,50,true);
  const submitted=h.submit();
  assert.equal(h.notes.saving,true);assert.equal(h.element('room-name').disabled,true);
  const count=h.requests.length;await h.submit();assert.equal(h.requests.length,count);
  await h.notes.select(300,50,true);assert.equal(h.requests.length,count);
  selection.resolve({...initial,name:'Obsolete selection'});await selecting;
  assert.equal(h.notes.room,selected);assert.equal(h.notes.point.x,100);
  saving.resolve({...initial,name:'Saved result',revision:3,room_notes_version:4});await submitted;
  assert.equal(h.notes.room.name,'Saved result');assert.equal(h.notes.saving,false);
  assert.equal(h.element('room-name').disabled,false);
});

test('a refresh begun before saving cannot clear the successfully saved selection',async()=>{
  const h=await fixture(),pending=deferred();
  h.api.get=path=>path.endsWith('/room-notes')?pending.promise:Promise.resolve({entries:[]});
  const refreshing=h.notes.refresh({cache_token:'background',walls_version:9,fog_version:9});
  h.api.post=async()=>({...initial,name:'Saved',revision:3,room_notes_version:4});
  await h.submit();
  const saved=h.notes.room;pending.resolve({rooms:[]});await refreshing;
  assert.equal(h.notes.room,saved);assert.equal(h.notes.room.name,'Saved');
  assert.equal(h.notes.point.x,100);assert.equal(h.element('room-read').hidden,false);
});

test('out-of-order selection responses cannot replace the latest selected context',async()=>{
  const h=await fixture(),first=deferred(),second=deferred();
  h.api.post=(path,body)=>body.x===200?first.promise:second.promise;
  const a=h.notes.select(200,50,true),b=h.notes.select(300,50,true);
  second.resolve({...initial,name:'Latest',cache_token:'latest-map',room_notes_version:8});await b;
  first.resolve({...initial,name:'Older',cache_token:'older-map'});await a;
  assert.equal(h.notes.room.name,'Latest');assert.equal(h.notes.room.cache_token,'latest-map');
  assert.equal(h.notes.room.room_notes_version,8);assert.equal(h.notes.point.x,300);
});

(async()=>{for(const entry of cases){await entry.run();console.log('PASS: '+entry.name);}
  console.log(`${cases.length} room-note save-context cases passed`);
})().catch(error=>{console.error(error);process.exitCode=1;});
