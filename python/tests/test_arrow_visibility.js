const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
const src=fs.readFileSync("static/js/admin_map_editor.js","utf8");
const controls=src.slice(src.indexOf("  function syncDoorArrowControls()"),src.indexOf('  vp.addEventListener("pointermove",'));
function app(admin,viewer,fail=false){
 const elements=new Map();const $=id=>{if(!elements.has(id))elements.set(id,{});return elements.get(id);};
 const ctx={$,busy:false,MAP_ID:1,state:{door_arrows_enabled:admin,viewer_door_arrows_enabled:viewer,
  door_arrow_color:"#46c0ff",locked_door_arrow_color:"#ff9f43"},calls:[]};
 ctx.LGApi={post:async(path,body)=>{
  ctx.calls.push(body);if(fail)throw Error("save failed");
  return {...ctx.state,...("admin_enabled" in body?{door_arrows_enabled:body.admin_enabled}:{}),
   ...("viewer_enabled" in body?{viewer_door_arrows_enabled:body.viewer_enabled}:{})};}};
 ctx.applyState=s=>{ctx.state=s;ctx.syncDoorArrowControls();};
 ctx.run=async fn=>{ctx.busy=true;ctx.syncDoorArrowControls();try{await fn();}catch(e){ctx.error=e;}finally{ctx.busy=false;}};
 vm.runInNewContext(controls,ctx);ctx.syncDoorArrowControls();return ctx;
}
(async()=>{
 for(const admin of [false,true])for(const viewer of [false,true]){
  const c=app(admin,viewer);
  assert.equal(c.$("door-arrows-enabled").checked,admin);
  assert.equal(c.$("viewer-door-arrows-enabled").checked,viewer);
  assert.equal(c.$("door-arrow-color").disabled,!admin&&!viewer);
  assert.equal(c.$("locked-door-arrow-color").disabled,!admin&&!viewer);
  c.busy=true;c.syncDoorArrowControls();
  assert.equal(c.$("door-arrows-enabled").disabled,true);assert.equal(c.$("viewer-door-arrows-enabled").disabled,true);
 }
 let c=app(true,true);c.$("door-arrows-enabled").checked=false;await c.$("door-arrows-enabled").onchange();
 assert.equal(c.calls[0].admin_enabled,false);assert.equal(c.state.door_arrows_enabled,false);assert.equal(c.state.viewer_door_arrows_enabled,true);
 c.$("viewer-door-arrows-enabled").checked=false;await c.$("viewer-door-arrows-enabled").onchange();assert.equal(c.state.viewer_door_arrows_enabled,false);
 c=app(true,true,true);c.$("viewer-door-arrows-enabled").checked=false;await c.$("viewer-door-arrows-enabled").onchange();
 assert.ok(c.error);assert.equal(c.$("viewer-door-arrows-enabled").checked,true);assert.equal(c.$("door-arrows-enabled").checked,true);
 console.log("Independent arrow controls, picker availability, busy and rollback tests passed");
})().catch(e=>{console.error(e);process.exitCode=1;});
