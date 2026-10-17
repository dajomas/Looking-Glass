// Run from repository root: node --test python/tests/test_viewer_refresh.js
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const tick = () => new Promise(resolve => setImmediate(resolve));

function viewer(states) {
  const elements = new Map(), images = [], intervals = [];
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
    PanZoom: class {setContentSize(){} fit(){}}, Image: FakeImage,
    WebSocket: class {}, console, setTimeout(){}, clearTimeout(){}, clearInterval(){},
    setInterval(fn, ms){intervals.push({fn,ms});},
    fetch: async () => ({ok: true, status:200, json: async () => states.shift()})};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../../static/js/viewer_display.js"), "utf8"), context);
  return {element, images, poll: () => intervals.find(i => i.ms===40000).fn()};
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
  const context = {window:{}, document:{getElementById:id => id==="map-display-dialog"?dialog:question,
    querySelectorAll:()=>[]}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../../static/js/map_display_prompt.js"),"utf8"),context);
  for (const action of ["restore","reset","cancel"]) {
    const result = context.window.LGChooseFog("<untrusted name>");
    dialog.returnValue=action; close();
    assert.equal(await result,action==="cancel"?null:action);
    assert.equal(question.textContent,'Show "<untrusted name>" to players?');
  }
});
