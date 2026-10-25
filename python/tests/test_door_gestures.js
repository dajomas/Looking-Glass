const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("static/js/admin_map_editor.js","utf8");
const tap=source.slice(source.indexOf("  function onTap("),source.indexOf("  const simple ="));
function makeClock(){let n=0;const tasks=new Map();return {setTimeout(fn){tasks.set(++n,fn);return n;},clearTimeout(id){tasks.delete(id);},flush(){const list=[...tasks.values()];tasks.clear();for(const fn of list)fn();}};}
async function check(kind,{double=false,hit="arrow",stale=false}={}){
 const clock=makeClock(),calls=[];
 const ctx={window:clock,console,areaTaps:{cancel(){}}};
 vm.runInNewContext(fs.readFileSync("static/js/door_gestures.js","utf8"),ctx);
 ctx.LGManagedDoorHit=ctx.window.LGManagedDoorHit;
 ctx.doorTapQueue=new ctx.window.LGDoorTapQueue(400,clock);
 Object.assign(ctx,{roomNotes:{editing:()=>false,select:async()=>{}},mapTransitions:null,state:{width:400,height:200,work_scale:1,cache_token:"map",walls_version:1,fog_version:1,
   door_arrows:[{wall_id:4,kind,polygon:[[160,90],[190,90],[190,110],[160,110]]}],
   managed_doors:[{wall_id:4,kind,x1:200,y1:80,x2:200,y2:120}]},
   MAP_ID:1,busy:false,maskKey:"map-1-1",stateKey:s=>`${s.cache_token}-${s.walls_version}-${s.fog_version}`,
   arrowHit:{at:()=>hit==="arrow"?{x:175,y:100}:null},mode:()=>"hide",pz:{scale:1},hiddenTypes:new Set(),$:()=>({checked:true}),
   LGApi:{post:async(path,body)=>{calls.push({path,body});return {door_action:body.gesture==="double"?(kind==="locked_door"?"unlock":"lock"):(kind==="locked_door"?"none":"reveal"),is_active:true};},get:async()=>ctx.state},
   applyState:()=>ctx.doorTapQueue.cancel(),toast:()=>{}});
 ctx.run=fn=>{ctx.pending=fn();};
 vm.runInNewContext(tap,ctx);
 const x=hit==="arrow"?175:200;
 ctx.onTap(x,100,{button:0});
 assert.equal(calls.length,0,"first click must not reveal immediately");
 if(double)ctx.onTap(x,100,{button:0});
 if(stale)ctx.state.fog_version++;
 clock.flush();if(ctx.pending)await ctx.pending;
 if(stale)assert.equal(calls.length,0);
 else {assert.equal(calls.length,1);assert.equal(calls[0].path,"/api/maps/1/door-action");assert.equal(calls[0].body.gesture,double?"double":"single");}
 return calls;
}
(async()=>{
 await check("locked_door");await check("locked_door",{double:true});
 await check("unlocked_door");await check("unlocked_door",{double:true});
 await check("unlocked_door",{double:true,hit:"wall"});await check("locked_door",{stale:true});
 const clock=makeClock(),ctx={window:clock};vm.runInNewContext(fs.readFileSync("static/js/door_gestures.js","utf8"),ctx);
 const q=new ctx.window.LGDoorTapQueue(400,clock);let action=0;
 q.tap("a","v",()=>action++,()=>action+=10);q.cancel();clock.flush();assert.equal(action,0);
 q.tap("a","v",()=>action++,()=>action+=10);q.tap("b","v",()=>action+=2,()=>action+=20);clock.flush();assert.equal(action,2);
 console.log("Managed-door click, double-click, wall, stale and cancellation tests passed");
})().catch(e=>{console.error(e);process.exitCode=1;});
