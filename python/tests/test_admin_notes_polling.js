// Run from repository root: node --test python/tests/test_admin_notes_polling.js
// Actual editor IIFE and room-notes class; isolated DOM, images and API transport.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../../static/js',name),'utf8');
const deferred=()=>{let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};};
async function settle(){for(let i=0;i<4;i++)await new Promise(setImmediate);}
const payload=(notes=3,fog=1)=>({id:1,campaign_id:1,name:'Map',cache_token:'same-map',
  image_version:'image-1',room_notes_version:notes,fog_version:fog,walls_version:7,
  width:400,height:200,work_width:400,work_height:200,work_scale:1,walls:[],op_count:fog,
  calibration:{offset_x:0,offset_y:0,scale_x:1,scale_y:1,doors_block:true},
  door_arrows_enabled:true,viewer_door_arrows_enabled:true,viewer_portal_arrows_enabled:false,
  viewer_secret_arrows_enabled:false,door_arrow_color:'#ffffff',locked_door_arrow_color:'#ff0000',
  live_viewers:0,is_active:true});
const room=(version=3)=>({area_key:'a'.repeat(64),cache_token:'same-map',walls_version:7,
  room_notes_version:version,revision:version-1,name:version===3?'Crypt':'Remote '+version,
  markdown:'Notes '+version,html:'<p>Notes '+version+'</p>',revealed:true});
async function fixture(){
  const elements=new Map(),maps=[],writes=[],calls=[],images=[],intervals=[];
  function element(id){
    if(!elements.has(id)){const classes=new Set();elements.set(id,{value:'1',checked:false,
      hidden:false,disabled:false,textContent:'',innerHTML:'',src:'',children:[],dataset:{},
      style:{setProperty(){}},classList:{toggle(k,on){on?classes.add(k):classes.delete(k);},
        contains(k){return classes.has(k);}},
      replaceChildren(){this.children=[];},appendChild(n){this.children.push(n);},
      setAttribute(k,v){this[k]=v;},removeAttribute(k){delete this[k];},focus(){},
      closest(){return element(id+'-label');},addEventListener(k,fn){this[k]=fn;},
      querySelectorAll(){return [];},selectedOptions:[{textContent:'Map'}],
      getBoundingClientRect(){return {width:800,height:600};},
      getContext(){return {clearRect(){},fillRect(){},drawImage(){}};}});}
    return elements.get(id);
  }
  const remote={room:room(),failLibrary:0,failRoom:0};
  class Queue{cancel(){}tap(){}}
  const portal={refresh(){},setBusy(){},setState(){},setMask(){}};
  const context={console,navigator:{},FormData:class{append(){}},
    window:{LG_MAP:{id:1,campaign_id:1},addEventListener(){}},
    document:{getElementById:element,createElement:()=>({value:'',textContent:''}),
      querySelectorAll(){return [];},querySelector(selector){return selector==='main.editor'?
        element('main'):{value:'reveal',checked:true};},activeElement:{tagName:'BODY'}},
    localStorage:{getItem(){return null;},setItem(){}},
    Image:class{constructor(){images.push(this);}decode(){return Promise.resolve();}},
    PanZoom:class{constructor(){this.scale=1;this.x=0;this.y=0;this.pointers=new Set();}
      setContentSize(w,h){this.w=w;this.h=h;}fit(){}zoomCenter(){}},
    LGDoorArrowHit:class{set(){}at(){return null;}},LGDoorTapQueue:Queue,LGAdminAreaTaps:Queue,
    LGWallAppearance(){},LGPortalCycle:{mount(){return portal;}},
    LGMapTransitions:{mount(){return {draw(){},tap(){return false;}};}},
    LGDoubleReveal(){return {refresh(){},redraw(){},selecting(){return false;},leaveSelection(){}};},
    setInterval(fn,ms){intervals.push({fn,ms});},setTimeout(){},clearTimeout(){},
    confirm(){throw Error('Background refresh must not request draft discard');},
    LGApi:{get(url){
      calls.push({method:'GET',url});
      if(url==='/api/maps/1'){const d=deferred();maps.push(d);return d.promise;}
      if(url.endsWith('/room-note-library')){
        if(remote.failLibrary){remote.failLibrary--;return Promise.reject(Error('library unavailable'));}
        return Promise.resolve({entries:[{id:1,name:'Crypt',markdown:'Import',assigned:true}]});
      }
      if(url.endsWith('/room-notes'))return Promise.resolve({rooms:[{area_key:remote.room.area_key,
        x:100,y:50,name:remote.room.name,active:true,revealed:true}]});
      throw Error('Unexpected GET '+url);
    },post(url,body){
      calls.push({method:'POST',url,body});
      if(url.endsWith('/room-at')){
        if(remote.failRoom){remote.failRoom--;return Promise.reject(Error('room unavailable'));}
        return Promise.resolve({...remote.room});
      }
      if(url.endsWith('/undo')){const d=deferred();writes.push(d);return d.promise;}
      throw Error('Unexpected mutation '+url);
    }}};
  vm.runInNewContext(read('room_notes.js'),context);
  context.LGRoomNotes=context.window.LGRoomNotes;
  vm.runInNewContext(read('admin_wall_renderer.js'),context);
  const source=read('admin_map_editor.js');
  assert.match(source,/\}\)\(\);\s*$/);
  vm.runInNewContext(source.replace(/\}\)\(\);\s*$/,
    'window.__notesPollingTest={roomNotes,snapshot:()=>({state,maskKey})};\n})();'),context);
  assert.equal(maps.length,1);maps[0].resolve(payload());await settle();
  const notes=context.window.__notesPollingTest.roomNotes;
  notes.point={x:100,y:50};notes.show({...remote.room});
  assert.equal(notes.room.name,'Crypt');
  const poll=()=>{const count=maps.length;const done=intervals.find(i=>i.ms===15000).fn();
    assert.equal(maps.length,count+1);return {request:maps.at(-1),done};};
  const update=async p=>{const pending=poll();pending.request.resolve(p);await pending.done;await settle();};
  return {notes,remote,calls,images,element,poll,update,writes,
    snapshot:()=>context.window.__notesPollingTest.snapshot()};
}

test('bug 27: a notes-only poll installs fresh selected content without new masks',async()=>{
  const h=await fixture(),mask=h.snapshot().maskKey,count=h.images.length;
  h.remote.room=room(4);await h.update(payload(4));
  assert.equal(h.snapshot().state.room_notes_version,4);
  assert.equal(h.notes.room.name,'Remote 4');
  assert.equal(h.element('room-preview').innerHTML,'<p>Notes 4</p>');
  assert.equal(h.snapshot().maskKey,mask);assert.equal(h.images.length,count);
});

test('bug 27: an identical poll retries a failed library read without repeating completed work',async()=>{
  const h=await fixture();h.remote.room=room(4);h.remote.failLibrary=1;
  await h.update(payload(4));
  assert.equal(h.snapshot().state.room_notes_version,4);assert.equal(h.notes.room.name,'Crypt');
  assert.match(h.element('toast').textContent,/library unavailable/);
  await h.update(payload(4));assert.equal(h.notes.room.name,'Remote 4');
  const calls=h.calls.length,images=h.images.length;
  await h.update(payload(4));
  assert.equal(h.calls.length,calls+1,'completed refresh must only request map metadata');
  assert.equal(h.images.length,images);
});

test('bug 27: an identical poll retries a failed selected-room read',async()=>{
  const h=await fixture();h.remote.room=room(4);h.remote.failRoom=1;
  await h.update(payload(4));assert.equal(h.notes.room.name,'Crypt');
  assert.match(h.element('toast').textContent,/room unavailable/);
  await h.update(payload(4));assert.equal(h.notes.room.name,'Remote 4');
});

test('bug 27: a refresh deferred during a room save retries on an identical poll',async()=>{
  const h=await fixture();h.remote.room=room(4);h.notes.saving=true;
  await h.update(payload(4));assert.equal(h.notes.room.name,'Crypt');
  h.notes.saving=false;await h.update(payload(4));
  assert.equal(h.notes.room.name,'Remote 4');
});

test('bug 27: a pre-action poll cannot replace newer notes context',async()=>{
  const h=await fixture(),old=h.poll();h.remote.room=room(5);
  const action=h.element('btn-undo').onclick();assert.equal(h.writes.length,1);
  h.writes[0].resolve(payload(5,2));await action;await settle();
  assert.equal(h.notes.room.room_notes_version,5);const count=h.calls.length;
  old.request.resolve(payload(4));await old.done;await settle();
  assert.equal(h.snapshot().state.room_notes_version,5);
  assert.equal(h.notes.room.room_notes_version,5);
  assert.equal(h.calls.length,count,'rejected stale poll must not start notes requests');
});
