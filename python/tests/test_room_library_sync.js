// Run from repository root: node --test python/tests/test_room_library_sync.js
// Regression-first contracts using real prototypes and a real manager instance.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../../static/js',name),'utf8');
const initial={area_key:'a'.repeat(64),cache_token:'same-map',walls_version:7,
  room_notes_version:3,revision:2,name:'Crypt',markdown:'Saved notes',html:'<p>Saved notes</p>',revealed:true};
const state=version=>({cache_token:'same-map',walls_version:7,fog_version:5,room_notes_version:version});
const entries=assigned=>[{id:1,name:'Crypt',markdown:'Imported notes',assigned,notes_match:false}];
class Element {
  constructor(){this.children=[];this.dataset={};this.events={};this.value='';this.checked=false;
    this.hidden=false;this.disabled=false;this.textContent='';this.innerHTML='';this.scrollTop=0;
    const classes=new Set();this.classList={toggle(k,on){on?classes.add(k):classes.delete(k);},contains(k){return classes.has(k);}};}
  appendChild(child){this.children.push(child);}
  replaceChildren(){this.children=[];}
  addEventListener(k,fn){this.events[k]=fn;}
  setAttribute(k,v){this[k]=v;}
  removeAttribute(k){delete this[k];}
  focus(){}
  closest(){return this;}
  querySelectorAll(tag){return this.children.flatMap(child=>[...(child.tag===tag?[child]:[]),...child.querySelectorAll(tag)]);}
  showModal(){this.open=true;}
  close(){this.open=false;this.events.close?.();}
}
async function fixture(){
  const nodes=new Map(),pending=[],notices=[];
  const node=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id);};
  const remote={room:{...initial},entries:entries(true),controlled:false};
  const context={window:{},confirm:()=>true,
    document:{getElementById:node,createElement:tag=>Object.assign(new Element(),{tag})},
    LGApi:{get(url){
      if(url.endsWith('/room-note-library')){
        if(remote.controlled)return new Promise((resolve,reject)=>pending.push({url,resolve,reject}));
        return Promise.resolve({entries:remote.entries});
      }
      if(url.endsWith('/room-notes'))return Promise.resolve({rooms:[{area_key:initial.area_key,
        x:100,y:50,name:remote.room.name,active:true,revealed:true}]});
      throw Error('Unexpected GET '+url);
    },post(url){
      if(url.endsWith('/room-at'))return Promise.resolve({...remote.room});
      throw Error('Background sync must not mutate: '+url);
    }}};
  vm.runInNewContext(read('room_notes.js'),context);
  vm.runInNewContext(read('room_library_manager.js'),context);
  // Seed only constructor state; all notes methods below are production methods.
  const notes=Object.create(context.window.LGRoomNotes.prototype);
  Object.assign(notes,{mapId:1,$:node,toast:(...args)=>notices.push(args),libraryGeneration:0,
    libraryEntries:[],saving:false,editMode:false,dirty:false,generation:0,draftVersion:0,
    refreshGeneration:0,stateStamp:null,notesStamp:null,fogStamp:null,staleNoticeStamp:null,
    revealed:null,room:null,point:{x:100,y:50}});
  const manager=new context.window.LGRoomLibraryManager(notes);notes.libraryManager=manager;
  notes.show({...initial});await notes.refresh(state(3));
  manager.dialog.showModal();await manager.refresh();
  assert.equal(notes.libraryEntries[0].assigned,true);assert.equal(manager.entries[0].assigned,true);
  remote.controlled=true;
  return {notes,manager,remote,pending,node,notices};
}

test('bug 27: notes-only remote unassign updates an open manager and picker together',async()=>{
  const h=await fixture();
  h.remote.room={...initial,name:'',markdown:'',html:'',revision:3,room_notes_version:4};
  const refreshing=h.notes.refresh(state(4));assert.equal(h.pending.length,1);
  h.pending[0].resolve({entries:entries(false)});await refreshing;
  assert.equal(h.notes.libraryEntries[0].assigned,false);
  assert.equal(h.manager.entries[0].assigned,false,'open manager must reflect accepted picker entries');
  assert.match(h.node('room-library-status').textContent,/0 assigned/);
  assert.equal(h.notes.room.name,'');
});

test('bug 27: an older manager read cannot roll back a newer picker result',async()=>{
  const h=await fixture(),dialog=h.manager.refresh(),picker=h.notes.loadLibrary();
  assert.equal(h.pending.length,2);
  h.pending[1].resolve({entries:entries(false)});await picker;
  h.pending[0].resolve({entries:entries(true)});await dialog;
  assert.equal(h.notes.libraryEntries[0].assigned,false,'late dialog result must not overwrite newer picker');
  assert.equal(h.manager.entries[0].assigned,false);assert.equal(h.manager.busy,false);
});

test('bug 27 safety: an older picker read cannot roll back a newer manager result',async()=>{
  const h=await fixture(),picker=h.notes.loadLibrary(),dialog=h.manager.refresh();
  assert.equal(h.pending.length,2);
  h.pending[1].resolve({entries:entries(false)});await dialog;
  h.pending[0].resolve({entries:entries(true)});await picker;
  assert.equal(h.notes.libraryEntries[0].assigned,false);
  assert.equal(h.manager.entries[0].assigned,false);assert.equal(h.manager.busy,false);
});

test('bug 27: a superseded manager failure cannot replace newer library status',async()=>{
  const h=await fixture(),dialog=h.manager.refresh(),picker=h.notes.loadLibrary();
  h.pending[1].resolve({entries:entries(false)});await picker;
  h.pending[0].reject(Error('obsolete dialog error'));await dialog;
  assert.doesNotMatch(h.node('room-library-status').textContent,/obsolete dialog error/);
  assert.equal(h.notes.libraryEntries[0].assigned,false);assert.equal(h.manager.entries[0].assigned,false);
  assert.equal(h.manager.busy,false);assert.equal(h.node('room-library-refresh').disabled,false);
});

test('bug 27: remote assignments converge without rebasing a dirty room draft',async()=>{
  const h=await fixture(),selected=h.notes.room;
  h.notes.editMode=true;h.node('room-name').value='My unsaved draft';
  h.node('room-markdown').value='Keep this text';h.notes.updateDirty();h.notes.draftVersion++;
  h.remote.room={...initial,room_notes_version:4,revision:3};
  const refreshing=h.notes.refresh(state(4));h.pending[0].resolve({entries:entries(false)});await refreshing;
  assert.equal(h.notes.room,selected);assert.equal(h.notes.room.room_notes_version,3);
  assert.equal(h.node('room-name').value,'My unsaved draft');assert.equal(h.node('room-markdown').value,'Keep this text');
  assert.equal(h.notes.dirty,true);assert.equal(h.notes.libraryEntries[0].assigned,false);
  assert.equal(h.manager.entries[0].assigned,false,'open manager must converge even with a dirty draft');
});
