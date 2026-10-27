const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const button={},status={};let resolve,calls=0;
const ctx={window:{},document:{getElementById:id=>id==="scrying-room-check"?button:status},LGApi:{post:()=>{calls++;return new Promise(r=>resolve=r);}}};
vm.runInNewContext(fs.readFileSync("static/js/scrying_glass_room.js","utf8"),ctx);
const ui=new ctx.window.LGScryingGlassRoom(1),room={area_key:"a".repeat(64),revision:2,name:"Room"};
(async()=>{
 ui.set(null,null,false,false);assert.equal(button.disabled,true);
 ui.set(room,{x:1,y:2},true,false);assert.equal(button.disabled,true);
 ui.set(room,{x:1,y:2},false,false);assert.equal(button.disabled,false);
 const pending=ui.check();assert.equal(button.disabled,true);await ui.check();assert.equal(calls,1);
 ui.set({...room,name:"Other",revision:3},{x:3,y:4},false,false);
 resolve({message:"OLD RESULT"});await pending;assert.notEqual(status.textContent,"OLD RESULT");assert.equal(button.disabled,false);
 const latest=ui.check();resolve({message:"Matching battle setup found"});await latest;assert.equal(status.textContent,"Matching battle setup found");
 ui.set(room,{x:1,y:2},false,true);assert.equal(button.disabled,true);
 console.log("Scrying Glass room UI guards and stale response rejection passed");
})().catch(e=>{console.error(e);process.exitCode=1;});
