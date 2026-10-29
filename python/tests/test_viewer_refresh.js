// Run from repository root: node --test python/tests/test_viewer_refresh.js
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const tick = () => new Promise(resolve => setImmediate(resolve));

function viewer(states) {
  const elements = new Map(), images = [], intervals = [], sockets = [];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {hidden: false, textContent: "", addEventListener(){},
      classList: {add(){}, remove(){}}, src: ""});
    return elements.get(id);
  };
  class FakeImage {
    constructor(){this.naturalWidth=400; this.naturalHeight=200; images.push(this);}
    decode(){return new Promise(resolve => {this.ready=resolve;});}
  }
  const context = {window: {LG_CAMPAIGN: 1, addEventListener(){}},
    document: {getElementById: element}, location: {protocol: "http:", host: "test", pathname: "/c/1"},
    PanZoom: class {constructor(){this.scale=1;this.x=0;this.y=0;this.minScale=.02;this.maxScale=8;}setContentSize(w,h){this.w=w;this.h=h;}apply(){}fit(){}}, Image: FakeImage,
    WebSocket: class {
      constructor(){this.readyState=1; this.reports=[]; sockets.push(this);}
      send(value){this.reports.push(JSON.parse(value));}
    }, console, setTimeout(){}, clearTimeout(){}, clearInterval(){},
    setInterval(fn, ms){intervals.push({fn,ms});},
    fetch: async () => {
      const result = states.shift();
      return {ok: !result?.httpError, status: result?.httpError || 200, json: async () => result};
    }};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../../static/js/viewer_area_zoom.js"), "utf8"), context);
  context.LGViewerAreaZoom=context.window.LGViewerAreaZoom;
  context.LGViewerDoubleTap=context.window.LGViewerDoubleTap;
  context.LGViewerHasNewAreas=context.window.LGViewerHasNewAreas;
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../../static/js/viewer_display.js"), "utf8"), context);
  return {element, images, report: () => sockets[0].reports.at(-1), poll: () => intervals.find(i => i.ms===40000).fn()};
}
const state = (name, version) => ({map:{name,version,image_url:`/${name}.png`}});

test("late old decode cannot overwrite the latest reveal", async () => {
  const app = viewer([state("old","1:token-1-1"),state("new","1:token-1-2")]);
  await tick(); app.poll(); await tick();
  app.images[1].ready(); await tick();
  assert.equal(app.element("map").src,"/new.png");
  app.images[0].ready(); await tick();
  assert.equal(app.element("map").src,"/new.png");
});

test("blanking prevents an older image from becoming visible", async () => {
  const app = viewer([state("old","1:old-1-1"),{map:null}]);
  await tick(); app.poll(); await tick();
  assert.equal(app.element("stage").hidden,true);
  app.images[0].ready(); await tick();
  assert.equal(app.element("stage").hidden,true);
});

test("display prompt resolves restore/reset and Escape as cancel", async () => {
  let close;
  const dialog = {returnValue:"", showModal(){}, addEventListener(name, fn){close=fn;}};
  const question = {};
  const context = {window:{}, fetch:async()=>({ok:true,json:async()=>({ok:true,can_restore:true})}), document:{getElementById:id => id==="map-display-dialog"?dialog:question,
    querySelectorAll:()=>[]}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../../static/js/map_display_prompt.js"),"utf8"),context);
  for (const action of ["restore","reset","cancel"]) {
    const result = context.window.LGChooseFog("<untrusted name>",1);
    await tick();
    dialog.returnValue=action; close();
    assert.equal(await result,action==="cancel"?null:action);
    assert.equal(question.textContent,'Show "<untrusted name>" to players?');
  }
});


test("destination prompts for current reveals even with empty checkpoint",async()=>{
 let close,shown=0,reads=0;
 const dialog={returnValue:"",showModal(){shown++;},addEventListener(name,fn){close=fn;}};
 const c={window:{},document:{getElementById:()=>dialog,querySelectorAll:()=>[]},fetch:async()=>{reads++;return {ok:true,json:async()=>({ok:true,can_restore:false,has_current_reveals:true})};}};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../../static/js/map_display_prompt.js"),"utf8"),c);
 assert.equal(await c.window.LGChooseFog("Prepared",2),"reset");assert.equal(shown,0);
 const result=c.window.LGChooseFog("Prepared",2,{includeCurrentReveals:true});await tick();
 assert.equal(shown,1);dialog.returnValue="cancel";close();assert.equal(await result,null);assert.equal(reads,2);
});

test("destination without any reveals skips the prompt",async()=>{
 const c={window:{},document:{getElementById:()=>({showModal(){throw Error("unexpected modal");}}),querySelectorAll:()=>[]},fetch:async()=>({ok:true,json:async()=>({ok:true,can_restore:false,has_current_reveals:false})})};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../../static/js/map_display_prompt.js"),"utf8"),c);
 assert.equal(await c.window.LGChooseFog("Empty",2,{includeCurrentReveals:true}),"reset");
});


for (const status of [500,404]) {
  test(`same-version recovery after HTTP ${status} waits for image installation`, async () => {
    const same=state("current","1:token-1-1");
    const app=viewer([same,{httpError:status},same]);
    await tick(); app.images[0].ready(); await tick();
    assert.equal(app.element("stage").hidden,false);
    await app.poll(); await tick();
    assert.equal(app.element("stage").hidden,true);
    assert.equal(app.element("waiting").hidden,false);
    assert.equal(app.report().state,"failed");
    const recovery=app.poll(); await tick();
    assert.equal(app.images.length,2);
    assert.equal(app.element("stage").hidden,true);
    assert.equal(app.report().state,"loading");
    assert.equal(app.element("sync-status").textContent,"Loading");
    app.images[1].ready(); await recovery; await tick();
    assert.equal(app.element("stage").hidden,false);
    assert.equal(app.element("waiting").hidden,true);
    assert.equal(app.element("map").src,"/current.png");
    assert.equal(app.report().state,"ready");
    assert.equal(app.report().version,same.map.version);
    assert.equal(app.element("sync-status").textContent,"Up to date");
  });
}

test("an already visible same-version image keeps the fast path", async () => {
  const same=state("current","1:token-1-1");
  const app=viewer([same,same]);
  await tick(); app.images[0].ready(); await tick();
  await app.poll(); await tick();
  assert.equal(app.images.length,1);
  assert.equal(app.element("stage").hidden,false);
  assert.equal(app.report().state,"ready");
});

test("a blank state after an HTTP error remains a truthful waiting screen", async () => {
  const app=viewer([state("current","1:token-1-1"),{httpError:500},{map:null}]);
  await tick(); app.images[0].ready(); await tick();
  await app.poll(); await tick();
  await app.poll(); await tick();
  assert.equal(app.images.length,1);
  assert.equal(app.element("stage").hidden,true);
  assert.equal(app.element("waiting").hidden,false);
  assert.equal(app.report().state,"ready");
  assert.equal(app.report().version,"blank");
});

test("a late recovery decode cannot overwrite a newer map", async () => {
  const same=state("current","1:token-1-1");
  const app=viewer([same,{httpError:500},same,state("new","2:other-1-1")]);
  await tick(); app.images[0].ready(); await tick();
  await app.poll(); await tick();
  const recovery=app.poll(); await tick();
  assert.equal(app.images.length,2);
  const newer=app.poll(); await tick();
  assert.equal(app.images.length,3);
  app.images[2].ready(); await newer; await tick();
  app.images[1].ready(); await recovery; await tick();
  assert.equal(app.element("map").src,"/new.png");
  assert.equal(app.element("stage").hidden,false);
  assert.equal(app.report().version,"2:other-1-1");
});
