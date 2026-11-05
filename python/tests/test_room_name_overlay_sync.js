// Run from repository root: node --test python/tests/test_room_name_overlay_sync.js
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../../static/js/room_name_overlay.js'),'utf8');
const tick=()=>new Promise(setImmediate);
const state=version=>({cache_token:'same-map',walls_version:7,room_notes_version:version,width:400,height:200});
async function fixture(){
  const nodes=new Map(),pending=[],errors=[];
  const node=id=>{if(!nodes.has(id))nodes.set(id,{hidden:true,checked:false,textContent:'',attrs:{},events:{},
    setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this[k];},
    addEventListener(k,fn){this.events[k]=fn;}});return nodes.get(id);};
  const context={window:{},document:{getElementById:node},
    LGApi:{get(url){return new Promise((resolve,reject)=>pending.push({url,resolve,reject}));}}};
  vm.runInNewContext(source,context);
  const overlay=new context.window.LGRoomNameOverlay(1,(...args)=>errors.push(args));
  overlay.mapChanged(state(3));
  node('room-select-mode').checked=true;node('room-select-mode').events.change();
  node('room-name-toggle').onclick();
  assert.equal(pending.length,1);
  pending[0].resolve({png:'initial',named:2,unnamed:3});await tick();
  assert.equal(node('room-name-overlay').hidden,false);
  return {overlay,node,pending,errors};
}

test('bug 27: notes-only revisions refresh overlay pixels and counts',async()=>{
  const h=await fixture();h.overlay.mapChanged(state(4));
  assert.equal(h.pending.length,2,'notes revision must invalidate overlay');
  assert.equal(h.node('room-name-overlay').hidden,true,'hide old coverage while refreshing');
  h.pending[1].resolve({png:'unassigned',named:1,unnamed:4});await tick();
  assert.equal(h.node('room-name-overlay').src,'data:image/png;base64,unassigned');
  assert.equal(h.node('room-name-overlay').hidden,false);
  assert.match(h.node('room-name-legend').textContent,/named \(1\).*unnamed \(4\)/);
  h.overlay.mapChanged(state(4));assert.equal(h.pending.length,2,'completed revision is cached');
});

for(const outcome of ['success','failure'])test(`bug 27: superseded overlay ${outcome} cannot replace newer coverage`,async()=>{
  const h=await fixture();h.overlay.mapChanged(state(4));h.overlay.mapChanged(state(5));
  assert.equal(h.pending.length,3);
  h.pending[2].resolve({png:'latest',named:0,unnamed:5});await tick();
  if(outcome==='success')h.pending[1].resolve({png:'obsolete',named:5,unnamed:0});
  else h.pending[1].reject(Error('obsolete error'));
  await tick();
  assert.equal(h.node('room-name-overlay').src,'data:image/png;base64,latest');
  assert.equal(h.node('room-name-overlay').hidden,false);assert.equal(h.errors.length,0);
  h.overlay.mapChanged(state(5));assert.equal(h.pending.length,3,'stale failure must not reset latest stamp');
});

test('bug 27: failed overlay fetch retries on an identical poll without duplicate in-flight work',async()=>{
  const h=await fixture();
  h.overlay.refresh();h.pending[1].reject(Error('temporary failure'));await tick();
  assert.equal(h.errors.length,1);assert.equal(h.node('room-name-overlay').hidden,true);
  h.overlay.mapChanged(state(3));assert.equal(h.pending.length,3,'same notes revision must retry');
  h.overlay.mapChanged(state(3));assert.equal(h.pending.length,3,'pending retry must not be duplicated');
  h.pending[2].resolve({png:'recovered',named:2,unnamed:3});await tick();
  assert.equal(h.node('room-name-overlay').src,'data:image/png;base64,recovered');
  h.overlay.mapChanged(state(3));assert.equal(h.pending.length,3);
});

test('bug 27: disabling coverage fences a pending notes-only refresh and does not auto-enable',async()=>{
  const h=await fixture();h.overlay.mapChanged(state(4));assert.equal(h.pending.length,2);
  h.node('room-select-mode').checked=false;h.node('room-select-mode').events.change();
  h.pending[1].resolve({png:'late',named:1,unnamed:4});await tick();
  h.overlay.mapChanged(state(5));
  assert.equal(h.pending.length,2);assert.equal(h.overlay.enabled,false);
  assert.equal(h.node('room-name-overlay').hidden,true);assert.equal(h.errors.length,0);
});
