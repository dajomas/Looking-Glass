// Run from repository root: node --test python/tests/test_admin_mask_identity.js
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"../../static/js/admin_map_editor.js"),"utf8");
const begin=source.indexOf("  async function loadMask() {"), end=source.indexOf("  function applyState(s) {",begin);
assert.ok(begin>=0 && end>begin,"production mask loader boundaries must exist");
const loader=source.slice(begin,end);
function setup() {
  const images=[], errors=[], installed=[], arrow={src:"/installed-A.png"};
  class Image {
    constructor(){images.push(this);}
    decode(){return new Promise((resolve,reject)=>{this.resolve=resolve;this.reject=reject;});}
  }
  const context={Image,MAP_ID:1,state:{key:"B"},stateKey:s=>s.key,maskGeneration:0,
    maskKey:"A",maskImg:{src:"/installed-A.png"},$:()=>arrow,
    arrowHit:{set(im,key){installed.push(key);}},
    portalCycle:{setMask(){},setState(){}},drawFog(){},loadError:msg=>errors.push(msg)};
  vm.runInNewContext(loader,context);
  return {context,images,errors,installed,arrow,load:()=>context.loadMask()};
}
test("identity change without a new request fences a successful old decode",async()=>{
  const app=setup(), pending=app.load();
  app.context.state={key:"C"};
  app.images.forEach(im=>im.resolve());await pending;
  assert.equal(app.context.maskKey,"A");
  assert.equal(app.context.maskImg.src,"/installed-A.png");
  assert.equal(app.arrow.src,"/installed-A.png");
  assert.deepEqual(app.installed,[]);
});
test("identity change without a new request suppresses an old decode failure",async()=>{
  const app=setup(), pending=app.load();
  app.context.state={key:"C"};
  app.images[0].reject(new Error("obsolete B"));app.images[1].resolve();
  await assert.doesNotReject(pending);
  assert.deepEqual(app.errors,[]);
  assert.equal(app.context.maskKey,"A");
});
test("late B failure cannot replace a newer C failure message",async()=>{
  const app=setup(), b=app.load();
  app.context.state={key:"C"};const c=app.load();
  app.images[2].reject(new Error("current C"));app.images[3].resolve();
  await assert.doesNotReject(c);
  assert.equal(app.errors.length,1);assert.match(app.errors[0],/current C/);
  app.images[0].reject(new Error("obsolete B"));app.images[1].resolve();
  await assert.doesNotReject(b);
  assert.equal(app.errors.length,1);assert.match(app.errors[0],/current C/);
});
test("current arrow decode failure does not partially install the fog mask",async()=>{
  const app=setup(), pending=app.load();
  app.images[0].resolve();app.images[1].reject(new Error("current arrow"));
  await assert.doesNotReject(pending);
  assert.equal(app.context.maskKey,"A");
  assert.equal(app.context.maskImg.src,"/installed-A.png");
  assert.equal(app.arrow.src,"/installed-A.png");assert.deepEqual(app.installed,[]);
  assert.equal(app.errors.length,1);assert.match(app.errors[0],/current arrow/);
});
