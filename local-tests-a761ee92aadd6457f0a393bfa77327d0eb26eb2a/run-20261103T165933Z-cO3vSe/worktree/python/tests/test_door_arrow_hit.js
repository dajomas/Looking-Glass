const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const context = {window: {}};
vm.runInNewContext(fs.readFileSync("static/js/door_arrow_hit.js", "utf8"), context);
const hit = new context.window.LGDoorArrowHit();
const data = new Uint8ClampedArray(20*10*4);
data[(5*20+8)*4+3] = 255;
hit.pixels = {width:20,height:10,data}; hit.key="current";
const state = {width:400,height:200,work_scale:.05,door_arrows_enabled:true};
let point = hit.at(170,110,state,"current");
assert.equal(point.x,170); assert.equal(point.y,110);
assert.equal(hit.at(100,100,state,"current"),null);
assert.equal(hit.at(170,110,state,"stale"),null);
assert.equal(hit.at(170,110,{...state,door_arrows_enabled:false},"current"),null);
for (const [x,y] of [[-1,110],[400,110],[170,200],[NaN,110],[170,Infinity]])
  assert.equal(hit.at(x,y,state,"current"),null);
console.log("Door arrow hit tests passed");
