// Run from repository root: node --test python/tests/test_room_notes_sync.js
// Regression-first bug 27 contracts; production code is intentionally unchanged.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../../static/js/room_notes.js'), 'utf8');
const original = {area_key:'a'.repeat(64), cache_token:'same-map', walls_version:7,
  room_notes_version:3, revision:2, name:'Crypt', markdown:'Original notes',
  html:'<p>Original notes</p>', revealed:true};
const state = version => ({cache_token:'same-map', walls_version:7, fog_version:5,
  room_notes_version:version});

async function fixture() {
  const elements = new Map(), requests = [], notices = [];
  function element(id) {
    if (!elements.has(id)) {
      const classes = new Set();
      elements.set(id, {value:'', checked:false, hidden:false, disabled:false,
        textContent:'', innerHTML:'', children:[],
        classList:{toggle(k,on){on?classes.add(k):classes.delete(k);},
          contains(k){return classes.has(k);}},
        replaceChildren(){this.children=[];}, appendChild(child){this.children.push(child);},
        setAttribute(k,v){this[k]=v;}, removeAttribute(k){delete this[k];}, focus(){},
        closest(){return element(id+'-label');}, addEventListener(k,fn){this[k]=fn;},
        querySelectorAll(){return ['room-name','room-markdown','room-save','room-cancel'].map(element);}});
    }
    return elements.get(id);
  }
  const remote = {room:{...original}, assigned:true};
  const entries = () => [{id:1, name:'Crypt', markdown:'Imported notes', assigned:remote.assigned}];
  const context = {window:{addEventListener(){}},
    document:{getElementById:element, querySelector:()=>element('main'),
      createElement:()=>({value:'',textContent:''})},
    localStorage:{getItem(){return null;},setItem(){}}, navigator:{},
    confirm(){throw Error('Background synchronization must not prompt to discard a draft');},
    FormData:class {append(){}},
    LGApi:{async get(url) {
      requests.push({method:'GET',url});
      if (url.endsWith('/room-note-library')) return {entries:entries()};
      if (url.endsWith('/room-notes')) return {rooms:[{area_key:original.area_key,
        name:remote.room.name, x:100, y:50, active:true, revealed:true}]};
      throw Error('Unexpected GET '+url);
    }, async post(url,body) {
      requests.push({method:'POST',url,body});
      if (url.endsWith('/room-at')) return {...remote.room};
      throw Error('Background synchronization must not save: '+url);
    }}};
  vm.runInNewContext(source, context);
  const notes = new context.window.LGRoomNotes(1,(...args)=>notices.push(args));
  await notes.loadLibrary();
  notes.point={x:100,y:50}; notes.show({...original});
  await notes.refresh(state(3));
  assert.equal(notes.room.name,'Crypt','baseline selected room must remain installed');
  assert.equal(notes.libraryEntries[0].assigned,true);
  return {notes,remote,element,requests,notices};
}

test('bug 27: a notes-only remote save refreshes a clean selected room', async () => {
  const h = await fixture();
  h.remote.room={...original,name:'Renamed crypt',markdown:'Saved in another editor',
    html:'<p>Saved in another editor</p>',revision:3,room_notes_version:4};
  await h.notes.refresh(state(4));
  assert.equal(h.notes.room.name,'Renamed crypt','notes-only revision must refresh selected content');
  assert.equal(h.element('room-preview').innerHTML,'<p>Saved in another editor</p>');
  assert.equal(h.notes.room.room_notes_version,4);
  assert.equal(h.notes.room.revision,3);
  assert.equal(h.notes.editMode,false);
  assert.equal(h.notes.dirty,false);
  assert.ok(!h.requests.some(r=>r.url.endsWith('/room-notes')&&r.method==='POST'));
});

test('bug 27: remote unassign clears clean content and releases the imported-name picker', async () => {
  const h = await fixture();
  h.remote.room={...original,name:'',markdown:'',html:'',revision:3,room_notes_version:4};
  h.remote.assigned=false;
  await h.notes.refresh(state(4));
  assert.equal(h.notes.room.name,'','remote unassign must clear the selected saved name');
  assert.equal(h.notes.room.markdown,'');
  assert.equal(h.element('room-preview').innerHTML,'');
  assert.equal(h.notes.libraryEntries[0].assigned,false,'remote unassign must refresh assignment availability');
  h.element('room-edit').onclick();
  assert.ok(h.element('room-import-select').children.some(option=>option.value==='1'),
    'released imported name must be selectable');
});

test('bug 27 safety: notes-only refresh preserves dirty text and its original save context', async () => {
  const h = await fixture();
  h.element('room-edit').onclick();
  h.element('room-name').value='Local draft'; h.element('room-name').oninput();
  h.element('room-markdown').value='Keep my unsaved text'; h.element('room-markdown').oninput();
  const selected=h.notes.room;
  h.remote.room={...original,name:'Remote edit',revision:3,room_notes_version:4};
  await h.notes.refresh(state(4));
  assert.equal(h.element('room-name').value,'Local draft');
  assert.equal(h.element('room-markdown').value,'Keep my unsaved text');
  assert.equal(h.notes.room,selected,'background refresh must not rebase the draft');
  assert.equal(h.notes.room.room_notes_version,3);
  assert.equal(h.notes.room.revision,2);
  assert.equal(h.notes.editMode,true);
  assert.equal(h.notes.dirty,true);
  assert.ok(!h.requests.some(r=>r.url.endsWith('/room-notes')&&r.method==='POST'));
});
