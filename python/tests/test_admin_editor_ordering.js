// Run from repository root: node --test python/tests/test_admin_editor_ordering.js
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const tick = () => new Promise(resolve => setImmediate(resolve));
const deferred = () => {let resolve, reject; const promise = new Promise((a,b) => {resolve=a; reject=b;}); return {promise,resolve,reject};};
const payload = (fog=1, token="incarnation-z", walls=1) => ({
  id:1, campaign_id:1, name:"Test map", cache_token:token, image_version:"image-1",
  fog_version:fog, walls_version:walls, width:400, height:200,
  work_width:400, work_height:200, work_scale:1, walls:[], op_count:fog,
  calibration:{offset_x:0,offset_y:0,scale_x:1,scale_y:1,doors_block:true},
  door_arrows_enabled:true, viewer_door_arrows_enabled:true,
  viewer_portal_arrows_enabled:false, viewer_secret_arrows_enabled:false,
  door_arrow_color:"#ffffff", locked_door_arrow_color:"#ff0000", live_viewers:0, is_active:true
});
function editor() {
  const elements=new Map(), images=[], intervals=[], gets=[], posts=[], fogDraws=[];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {
      value:"1", checked:true, hidden:false, textContent:"", src:"", width:0, height:0,
      style:{setProperty(){}}, classList:{contains(){return false;}}, dataset:{},
      selectedOptions:[{textContent:"Test map"}], namespaceURI:"http://www.w3.org/2000/svg",
      addEventListener(){}, setAttribute(){}, appendChild(){}, querySelectorAll(){return [];},
      getBoundingClientRect(){return {width:800,height:600};},
      getContext(){return {clearRect(){},fillRect(){},drawImage(im){fogDraws.push(im.src);}}}
    });
    return elements.get(id);
  };
  class FakeImage {
    constructor(){this.pending=deferred(); images.push(this);}
    decode(){return this.pending.promise;}
  }
  class CancelQueue {cancel(){} tap(){}}
  const portal={refresh(){},setBusy(){},setState(){},setMask(){}};
  const transitions={draw(){},tap(){return false;}};
  const doubleReveal={refresh(){},redraw(){},selecting(){return false;},leaveSelection(){}};
  const context={console, Image:FakeImage, localStorage:{getItem(){return null;},setItem(){}},
    window:{LG_MAP:{id:1,campaign_id:1},addEventListener(){}},
    document:{getElementById:element,querySelectorAll(){return [];},
      querySelector(){return {value:"reveal",checked:true};},activeElement:{tagName:"BODY"}},
    PanZoom:class {constructor(){this.scale=1;this.x=0;this.y=0;this.pointers=new Set();}setContentSize(w,h){this.w=w;this.h=h;}fit(){}zoomCenter(){}},
    LGDoorArrowHit:class {set(){}at(){return null;}},LGDoorTapQueue:CancelQueue,LGAdminAreaTaps:CancelQueue,
    LGWallAppearance(){}, LGPortalCycle:{mount(){return portal;}},LGMapTransitions:{mount(){return transitions;}},
    LGRoomNotes:class {refresh(){}editing(){return false;}async select(){}},LGDoubleReveal(){return doubleReveal;},
    LGApi:{get(url){const d=deferred();gets.push({url,...d});return d.promise;},
      post(url,body){const d=deferred();posts.push({url,body,...d});return d.promise;}},
    setInterval(fn,ms){intervals.push({fn,ms});},setTimeout(){},clearTimeout(){},confirm(){return true;}
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../../static/js/admin_wall_renderer.js"),"utf8"),context);
  // Test-only observation/control seam; the complete production IIFE still runs.
  const source=fs.readFileSync(path.join(__dirname,"../../static/js/admin_map_editor.js"),"utf8");
  assert.match(source,/\}\)\(\);\s*$/);
  vm.runInNewContext(source.replace(/\}\)\(\);\s*$/,
    'window.__editorTest = {applyState, snapshot: () => ({state, maskKey})};\n})();'),context);
  return {element,images,gets,posts,fogDraws,
    poll:()=>intervals.find(i=>i.ms===15000).fn(),
    install:s=>context.window.__editorTest.applyState(s),
    snapshot:()=>context.window.__editorTest.snapshot()};
}
async function boot(s=payload()) {
  const app=editor();
  assert.equal(app.gets.length,1,"boot must request map state");
  app.gets[0].resolve(s); await tick();
  assert.equal(app.images.length,2,"boot must load fog and arrow masks");
  app.images.slice(0,2).forEach(im=>im.pending.resolve()); await tick();
  assert.equal(app.snapshot().state.cache_token,s.cache_token);
  assert.ok(app.snapshot().maskKey,"initial mask must be installed");
  return app;
}
function pendingPoll(app) {
  const before=app.gets.length, done=app.poll();
  assert.equal(app.gets.length,before+1,"idle poll must issue a request");
  return {request:app.gets.at(-1),done};
}

test("bug 25: a pre-action poll cannot roll back the action result",async()=>{
  const app=await boot(), old=pendingPoll(app);
  const action=app.element("btn-undo").onclick();
  assert.equal(app.posts.at(-1).url,"/api/maps/1/undo");
  app.posts.at(-1).resolve(payload(3)); await action; await tick();
  assert.equal(app.snapshot().state.fog_version,3);
  old.request.resolve(payload(2)); await old.done; await tick();
  assert.equal(app.snapshot().state.fog_version,3);
  assert.equal(app.element("op-count").textContent,3);
});

test("bug 25: a poll completing during a mutation cannot replace state",async()=>{
  const app=await boot(), old=pendingPoll(app);
  const action=app.element("btn-undo").onclick();
  old.request.resolve(payload(2)); await old.done; await tick();
  const during=app.snapshot().state.fog_version;
  app.posts.at(-1).resolve(payload(3)); await action;
  assert.equal(during,1,"pending mutation must fence an older poll");
  assert.equal(app.snapshot().state.fog_version,3);
});

test("bug 25: overlapping polls cannot install the older response last",async()=>{
  const app=await boot(), first=pendingPoll(app);
  const count=app.gets.length, secondDone=app.poll();
  if(app.gets.length===count){
    first.request.resolve(payload(2)); await first.done; await secondDone;
    assert.equal(app.snapshot().state.fog_version,2);
    return; // Serializing polling is also an acceptable ordering policy.
  }
  app.gets.at(-1).resolve(payload(3)); await secondDone;
  first.request.resolve(payload(2)); await first.done; await tick();
  assert.equal(app.snapshot().state.fog_version,3);
});

test("bug 25: equal revisions with a replacement incarnation still refresh",async()=>{
  const app=await boot(payload(1,"incarnation-z")), poll=pendingPoll(app);
  poll.request.resolve(payload(1,"incarnation-a")); await poll.done; await tick();
  assert.equal(app.snapshot().state.cache_token,"incarnation-a");
});

test("bug 25: late previous-incarnation poll cannot undo replacement",async()=>{
  const app=await boot(payload(7,"incarnation-z")), old=pendingPoll(app);
  const action=app.element("btn-undo").onclick();
  app.posts.at(-1).resolve(payload(1,"incarnation-a")); await action;
  old.request.resolve(payload(8,"incarnation-z")); await old.done; await tick();
  assert.equal(app.snapshot().state.cache_token,"incarnation-a");
  assert.equal(app.snapshot().state.fog_version,1);
});

test("bug 25: ordinary external-DM fog and wall changes still converge",async()=>{
  const app=await boot(), poll=pendingPoll(app);
  poll.request.resolve(payload(2,"incarnation-z",2)); await poll.done; await tick();
  assert.equal(app.snapshot().state.fog_version,2);
  assert.equal(app.snapshot().state.walls_version,2);
});

test("bug 26: A to pending B to cached A cannot install decoded B",async()=>{
  const a=payload(), app=await boot(a), original=app.snapshot().maskKey;
  const originalArrow=app.element("door-arrows").src;
  app.install(payload(2)); await tick();
  assert.equal(app.images.length,4);
  app.install(a); await tick();
  app.images.slice(2,4).forEach(im=>im.pending.resolve()); await tick();
  assert.equal(app.snapshot().state.fog_version,1);
  assert.equal(app.snapshot().maskKey,original);
  assert.equal(app.element("door-arrows").src,originalArrow);
  assert.match(app.fogDraws.at(-1),new RegExp(`v=${original}$`));
});

test("bug 26: failure of superseded B after cached A does not show an error",async()=>{
  const a=payload(),app=await boot(a), original=app.snapshot().maskKey;
  app.install(payload(2)); await tick(); app.install(a); await tick();
  app.images[2].pending.reject(new Error("obsolete decode"));
  app.images[3].pending.resolve(); await tick();
  assert.equal(app.snapshot().maskKey,original);
  assert.equal(app.element("map-load-error").hidden,true);
});

test("bug 26: newer C mask wins when B finishes decoding later",async()=>{
  const app=await boot(); app.install(payload(2)); await tick();
  app.install(payload(3)); await tick();
  app.images.slice(4,6).forEach(im=>im.pending.resolve()); await tick();
  const current=app.snapshot().maskKey, arrow=app.element("door-arrows").src;
  app.images.slice(2,4).forEach(im=>im.pending.resolve()); await tick();
  assert.equal(app.snapshot().maskKey,current);
  assert.equal(app.element("door-arrows").src,arrow);
  assert.equal(app.snapshot().state.fog_version,3);
});

test("bug 26: a current mask decode failure remains visible",async()=>{
  const app=await boot(); app.install(payload(2)); await tick();
  app.images[2].pending.reject(new Error("current decode"));
  app.images[3].pending.resolve(); await tick();
  assert.equal(app.element("map-load-error").hidden,false);
  assert.match(app.element("map-load-error").textContent,/current decode/);
});
