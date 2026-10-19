// Exercise the production tap handler with mocked transport/UI, not a browser.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("static/js/admin_map_editor.js", "utf8");
const tap = source.slice(source.indexOf("  function onTap("), source.indexOf("  const simple ="));
const state = {width:400,height:200,cache_token:"map",walls_version:1,fog_version:1};
function setup({hit=true,button=0,mode="hide",stale=false,reject=false}={}) {
  const calls=[],notices=[];
  const ctx={state:{...state},busy:false,maskKey:stale?"old":"map-1-1",MAP_ID:1,
    stateKey:s=>`${s.cache_token}-${s.walls_version}-${s.fog_version}`,
    areaTaps:{cancel(){},tap(x,y,stamp,single){single();}},LGManagedDoorHit:()=>null,pz:{scale:1},$:()=>({checked:true}),hiddenTypes:new Set(),doorTapQueue:{cancel(){}},
    mode:()=>mode,arrowHit:{at:()=>hit?{x:175.5,y:100.5}:null},
    LGApi:{post:async(path,body)=>{calls.push({path,body});if(reject)throw Error("stale");return {area_fraction:.2,is_active:true};},
      get:async()=>({refreshed:true})},
    applyState:s=>notices.push(s),toast:()=>{}};
  ctx.run=fn=>{ctx.pending=fn().catch(e=>{ctx.error=e;});};
  vm.runInNewContext(tap,ctx);
  ctx.onTap(175,100,{button});
  return {ctx,calls,notices};
}
(async()=>{
  let t=setup();await t.ctx.pending;
  assert.equal(t.calls.length,1);
  assert.equal(t.calls[0].path,"/api/maps/1/door-arrows/reveal");
  assert.equal(t.calls[0].body.fog_version,1);
  assert.equal(t.calls[0].body.x,175.5);
  t=setup({hit:false});await t.ctx.pending;
  assert.equal(t.calls[0].path,"/api/maps/1/hide");
  t=setup({button:2,mode:"reveal"});await t.ctx.pending;
  assert.equal(t.calls[0].path,"/api/maps/1/hide");
  t=setup({stale:true});assert.equal(t.calls.length,0);
  t=setup({reject:true});await t.ctx.pending;
  assert.equal(t.calls.length,1); // No normal hide/reveal fallback.
  assert.equal(t.notices[0].refreshed,true);assert.ok(t.ctx.error);
  console.log("Door arrow tap handler tests passed");
})().catch(e=>{console.error(e);process.exitCode=1;});
