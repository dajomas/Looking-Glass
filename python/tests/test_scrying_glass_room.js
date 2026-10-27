const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("static/js/scrying_glass_room.js","utf8");
const flush=()=>new Promise(r=>setImmediate(r));
const room={area_key:"a".repeat(64),revision:1,name:"Guard Room"};
class Element {
 constructor(){this.children=[];this.hidden=false;this.textContent="";}
 append(...items){this.children.push(...items);}
 replaceChildren(...items){this.children=items;}
 set innerHTML(value){throw Error("Unsafe HTML rendering");}
}
function make(handler) {
 const status=new Element(),results=new Element(),calls=[];let now=100000;
 const ctx={window:{},Date:{now:()=>now},document:{getElementById:id=>{
  if(id==="scrying-room-status")return status;if(id==="scrying-room-results")return results;throw Error(id);
 },createElement:()=>new Element()},LGApi:{post:(url,body)=>{calls.push({url,body});return Promise.resolve().then(()=>handler(url,body));}}};
 vm.runInNewContext(source,ctx);return {ui:new ctx.window.LGScryingGlassRoom(1),status,results,calls,advance:ms=>now+=ms};
}
(async()=>{
 let x=make(()=>{throw Error("must not call");});
 x.ui.set(null,null,false,false);x.ui.set({...room,name:" "},{x:1,y:2},false,false);
 x.ui.set(room,{x:1,y:2},true,false);x.ui.set(room,{x:1,y:2},false,true);await flush();assert.equal(x.calls.length,0);
 x=make(()=>({enabled:false,verified:false,retry_after_seconds:60}));x.ui.set(room,{x:1,y:2},false,false);await flush();
 assert.equal(x.calls.length,1);assert.equal(x.status.hidden,true);assert.equal(x.results.hidden,true);
 x.ui.set({...room,area_key:"b",name:"Other"},{x:3,y:4},false,false);await flush();assert.equal(x.calls.length,1);
 x=make(()=>({enabled:true,verified:false,message:"No campaign access",retry_after_seconds:30}));
 x.ui.set(room,{x:1,y:2},false,false);await flush();assert.equal(x.calls.length,1);assert.equal(x.status.textContent,"No campaign access");assert.equal(x.results.hidden,true);
 x=make(url=>url.endsWith("/access")?{enabled:true,verified:true,retry_after_seconds:60}:{enabled:true,verified:true,message:"FOUND",retry_after_seconds:60});
 x.ui.set(room,{x:1,y:2},false,false);await flush();assert.deepEqual(x.calls.map(c=>c.url.split("/").pop()),["access","check"]);assert.equal(x.status.textContent,"FOUND");
 x.ui.set(room,{x:20,y:30},false,false);await flush();assert.equal(x.calls.length,2);
 const other={...room,area_key:"b",name:"Other"};x.ui.set(other,{x:2,y:3},false,false);await flush();assert.equal(x.calls.length,3);
 x.ui.set(room,{x:1,y:2},false,false);await flush();assert.equal(x.calls.length,3);
 x.advance(61000);x.ui.set(room,{x:1,y:2},false,false);await flush();assert.equal(x.calls.length,5);
 x=make(()=>{throw Error("login failed");});x.ui.set(room,{x:1,y:2},false,false);await flush();
 x.ui.set(other,{x:2,y:3},false,false);await flush();assert.equal(x.calls.length,1);
 x.advance(31000);x.ui.set(other,{x:2,y:3},false,false);await flush();assert.equal(x.calls.length,2);
 let resolveAccess,resolveCheck;x=make(url=>url.endsWith("/access")?new Promise(r=>resolveAccess=r):new Promise(r=>resolveCheck=r));
 x.ui.set(room,{x:1,y:2},false,false);await flush();x.ui.set(other,{x:2,y:3},false,false);await flush();assert.equal(x.calls.length,1);
 resolveAccess({enabled:true,verified:true,retry_after_seconds:60});await flush();assert.equal(x.calls.length,2);assert.equal(x.calls[1].body.area_key,"b");
 x.ui.set(null,null,false,false);resolveCheck({message:"STALE",matched:true,setup_names:["stale"],retry_after_seconds:60});await flush();
 assert.notEqual(x.status.textContent,"STALE");assert.equal(x.results.hidden,true);
 // Prominent, plural results and cache restore use the full response, never HTML strings.
 const names=["guard-room","guard-room-1-4","guard-room-5-6","guard-room-<img onerror=alert(1)>"];
 x=make(url=>url.endsWith("/access")?{enabled:true,verified:true,retry_after_seconds:60}:
   {enabled:true,verified:true,matched:true,setup_name:"guard-room",setup_names:names,message:"4 matching",retry_after_seconds:60});
 x.ui.set(room,{x:1,y:2},false,false);await flush();assert.equal(x.results.hidden,false);assert.equal(x.status.hidden,true);
 assert.equal(x.results.children[0].children[0].textContent,"✓ 4 battle setups found");
 const list=x.results.children[1];assert.equal(list.children.length,4);
 assert.equal(list.children[0].children[1].textContent,"Exact match");assert.equal(list.children[3].children[0].textContent,names[3]);
 x.ui.set(other,{x:2,y:3},true,false);assert.equal(x.results.hidden,true);
 x.ui.set(room,{x:9,y:9},false,false);await flush();assert.equal(x.calls.length,2);assert.equal(x.results.children[1].children.length,4);
 x.ui.render({matched:false,message:"No setup found"});assert.equal(x.results.hidden,true);assert.equal(x.results.children.length,0);
 x.ui.render({matched:true,setup_name:"guard-room",setup_names:["guard-room"],message:"one"});
 assert.equal(x.results.children[0].children[0].textContent,"✓ Battle setup found");
 console.log("Automatic gate/backoff/cache, prefix-list rendering, exact markers and safe stale-result regressions passed");
})().catch(e=>{console.error(e);process.exitCode=1;});
