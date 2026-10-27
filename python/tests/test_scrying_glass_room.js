const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("static/js/scrying_glass_room.js","utf8");
const flush=()=>new Promise(r=>setImmediate(r));
const room={area_key:"a".repeat(64),revision:1,name:"Guard Room"};
function make(handler) {
 const status={},calls=[];let now=100000;
 const ctx={window:{},Date:{now:()=>now},document:{getElementById:id=>{assert.equal(id,"scrying-room-status");return status;}},
   LGApi:{post:(url,body)=>{calls.push({url,body});return Promise.resolve().then(()=>handler(url,body));}}};
 vm.runInNewContext(source,ctx);
 return {ui:new ctx.window.LGScryingGlassRoom(1),status,calls,advance:ms=>now+=ms};
}
(async()=>{
 let x=make(()=>{throw Error("must not call");});
 x.ui.set(null,null,false,false);x.ui.set({...room,name:" "},{x:1,y:2},false,false);
 x.ui.set(room,{x:1,y:2},true,false);x.ui.set(room,{x:1,y:2},false,true);await flush();assert.equal(x.calls.length,0);
 x=make(()=>({enabled:false,verified:false,retry_after_seconds:60}));
 x.ui.set(room,{x:1,y:2},false,false);await flush();assert.equal(x.calls.length,1);assert.equal(x.status.hidden,true);
 x.ui.set({...room,area_key:"b",name:"Other"},{x:3,y:4},false,false);await flush();assert.equal(x.calls.length,1);
 x=make(()=>({enabled:true,verified:false,message:"No campaign access",retry_after_seconds:30}));
 x.ui.set(room,{x:1,y:2},false,false);await flush();assert.equal(x.calls.length,1);assert.equal(x.status.textContent,"No campaign access");
 x=make(url=>url.endsWith("/access")?{enabled:true,verified:true,retry_after_seconds:60}:{enabled:true,verified:true,message:"FOUND",retry_after_seconds:60});
 x.ui.set(room,{x:1,y:2},false,false);await flush();
 assert.deepEqual(x.calls.map(c=>c.url.split("/").pop()),["access","check"]);assert.equal(x.status.textContent,"FOUND");
 x.ui.set(room,{x:20,y:30},false,false);await flush();assert.equal(x.calls.length,2);
 const other={...room,area_key:"b",name:"Other"};x.ui.set(other,{x:2,y:3},false,false);await flush();assert.equal(x.calls.length,3);
 x.ui.set(room,{x:1,y:2},false,false);await flush();assert.equal(x.calls.length,3);
 x.advance(61000);x.ui.set(room,{x:1,y:2},false,false);await flush();assert.equal(x.calls.length,5);
 x=make(()=>{throw Error("login failed");});x.ui.set(room,{x:1,y:2},false,false);await flush();
 x.ui.set(other,{x:2,y:3},false,false);await flush();assert.equal(x.calls.length,1);
 x.advance(31000);x.ui.set(other,{x:2,y:3},false,false);await flush();assert.equal(x.calls.length,2);
 // Switching rooms while verification is pending shares one gate and checks only the newest room.
 let resolveAccess,resolveCheck;
 x=make(url=>url.endsWith("/access")?new Promise(r=>resolveAccess=r):new Promise(r=>resolveCheck=r));
 x.ui.set(room,{x:1,y:2},false,false);await flush();x.ui.set(other,{x:2,y:3},false,false);await flush();assert.equal(x.calls.length,1);
 resolveAccess({enabled:true,verified:true,retry_after_seconds:60});await flush();assert.equal(x.calls.length,2);
 assert.equal(x.calls[1].body.area_key,"b");
 x.ui.set(null,null,false,false);resolveCheck({message:"STALE",retry_after_seconds:60});await flush();assert.notEqual(x.status.textContent,"STALE");assert.equal(x.status.hidden,true);
 console.log("Automatic Scrying Glass gates, deduplication, TTL, backoff and stale-response tests passed");
})().catch(e=>{console.error(e);process.exitCode=1;});
