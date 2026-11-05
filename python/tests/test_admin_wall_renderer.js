// Run from repository root: node --test python/tests/test_admin_wall_renderer.js
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
function setup() {
  const fields = new Map(), children = [];
  const $ = id => {if (!fields.has(id)) fields.set(id,{value:"",checked:false});return fields.get(id);};
  const svg = {namespaceURI:"svg",innerHTML:"",appendChild(node){children.push(node);}};
  const pz = {scale:2}, hiddenTypes = new Set();
  let state = {}, walls = [], widths = 0;
  const context = {window:{},document:{createElementNS(ns,tag){return {ns,tag,attrs:{},setAttribute(k,v){this.attrs[k]=v;}};}}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../../static/js/admin_wall_renderer.js"),"utf8"),context);
  const renderer = context.window.LGAdminWallRenderer({$,svg,pz,hiddenTypes,getState:()=>state,
    getRawWalls:()=>walls,updateWallWidth:()=>widths++});
  return {...renderer,$,svg,pz,hiddenTypes,children,widths:()=>widths,
    state:s=>{state=s;},walls:w=>{walls=w;}};
}
test("calibration keeps existing fallback and rounding behavior",()=>{
  const app=setup();
  assert.equal(JSON.stringify(app.cal()),JSON.stringify({offset_x:0,offset_y:0,scale_x:1,scale_y:1,doors_block:false}));
  app.fillCalibration({offset_x:1.234567,offset_y:-2.345678,scale_x:1.23456789,scale_y:2.34567891,doors_block:true});
  assert.equal(app.$("cal-ox").value,1.2346);
  assert.equal(app.$("cal-oy").value,-2.3457);
  assert.equal(app.$("cal-sx").value,1.234568);
  assert.equal(app.$("cal-sy").value,2.345679);
  assert.equal(app.cal().doors_block,true);
});
test("walls retain calibrated coordinates, grouping and hidden-type filtering",()=>{
  const app=setup();
  app.fillCalibration({offset_x:10,offset_y:20,scale_x:2,scale_y:3,doors_block:true});
  app.walls([[10,20,20,30,"wall",true],[20,30,30,40,"wall",true],[0,0,1,1,"window",true]]);
  app.hiddenTypes.add("window");app.renderWalls();
  assert.equal(app.svg.innerHTML,'<path class="w-wall" d="M0.0 0.0L20.0 30.0M20.0 30.0L40.0 60.0"/>');
  assert.equal(app.widths(),1);
});
test("fresh state and wall getters preserve passive and locked-door styling",()=>{
  const app=setup();
  app.fillCalibration({offset_x:0,offset_y:0,scale_x:1,scale_y:1,doors_block:true});
  app.walls([[0,0,10,10,"wall",true]]);app.renderWalls();
  assert.match(app.svg.innerHTML,/w-wall/);
  app.state({disabled_wall_types:["wall"]});app.renderWalls();
  assert.match(app.svg.innerHTML,/w-passive/);
  app.walls([[0,0,10,10,"locked_door",false]]);app.renderWalls();
  assert.match(app.svg.innerHTML,/w-locked_door passive/);
  app.$("cal-doors").checked=false;
  app.walls([[0,0,10,10,"door",true]]);app.renderWalls();
  assert.match(app.svg.innerHTML,/w-passive/);
  assert.equal(app.widths(),4);
});
test("portal side roles, offsets and hidden portal filtering are preserved",()=>{
  const app=setup();
  app.state({portal_styles:[{x1:0,y1:0,x2:10,y2:0,sides:[{role:"entry",kind:"secret"},{role:"exit",kind:"locked_door"}]}]});
  app.renderWalls();
  assert.equal(app.children.length,2);
  assert.equal(app.children[0].attrs.class,"portal-side p-secret");
  assert.equal(app.children[0].attrs.d,"M0 -1L10 -1");
  assert.equal(app.children[1].attrs.class,"portal-side p-door");
  assert.equal(app.children[1].attrs.d,"M0 1L10 1");
  app.hiddenTypes.add("portal");app.renderWalls();
  assert.equal(app.children.length,2);
});
