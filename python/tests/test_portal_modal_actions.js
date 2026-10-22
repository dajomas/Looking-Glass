const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
const elements=new Map();
class El{
 constructor(tag="",id=""){this.tagName=tag;this.children=[];this.value="";this.events={};this.open=false;this.scrollTop=0;this.id=id;}
 set id(v){this._id=v;if(v)elements.set(v,this);}get id(){return this._id;}
 appendChild(e){this.children.push(e);}replaceChildren(){this.children=[];}
 addEventListener(k,fn){this.events[k]=fn;}focus(){}showModal(){this.open=true;}
 close(){this.open=false;this.events.close?.();}
}
const get=id=>elements.get(id)||new El("",id);
let answer=true;const prompts=[];let walls=[[10,10,10,90,"portal",true,{sides:[{role:"unconfigured"},{role:"unconfigured"}]}],[90,10,90,90,"portal",true,{sides:[{role:"unconfigured"},{role:"unconfigured"}]}]];
let mutations=0;
const c={console,structuredClone,Uint8Array,crypto:{getRandomValues:a=>a.fill(1)},window:{},document:{getElementById:get,activeElement:null,createElement:tag=>new El(tag)}};
c.window.confirm=message=>{prompts.push(message);return answer;};c.window.LGFloatingDialog=dialog=>({open:()=>dialog.showModal()});c.window.LGPortalOverview={mount:()=>({open(){}})};
vm.createContext(c);vm.runInContext(fs.readFileSync("static/js/portal_editor.js","utf8"),c);
c.window.LGPortalEditor({getWalls:()=>walls,getBusy:()=>false,mutate:change=>{walls=structuredClone(change.after);mutations++;},status(){},viewport:{focus(){}}});
const open=()=>get("portal-configure").onclick();
open();assert.equal(get("portal-dialog").open,true);get("portal-close").onclick();assert.equal(prompts.length,0);assert.equal(get("portal-dialog").open,false);
open();get("portal-side-0-role").value="entry";get("portal-side-0-role").onchange();
answer=false;get("portal-close").onclick();assert.equal(get("portal-dialog").open,true);assert.match(prompts.at(-1),/Discard unapplied/);
let prevented=false;get("portal-dialog").events.cancel({preventDefault(){prevented=true;}});assert.ok(prevented);assert.equal(get("portal-dialog").open,true);
get("portal-form").onsubmit({preventDefault(){}});assert.equal(mutations,1);assert.equal(get("portal-dialog").open,true);
const count=prompts.length;get("portal-close").onclick();assert.equal(prompts.length,count);assert.equal(get("portal-dialog").open,false);
open();get("portal-side-0-kind").value="secret";get("portal-side-0-kind").onchange();answer=true;get("portal-close").onclick();assert.equal(walls[0][6].sides[0].kind,"door");assert.equal(mutations,1);
// Paired reset names every affected section and is staged only after confirmation.
walls=[[10,10,10,90,"portal",true,{pair:"p",end:"a",sides:[{role:"entry",kind:"door",after:"door",exit:0},{role:"none"}]}],[90,10,90,90,"portal",true,{pair:"p",end:"b",sides:[{role:"exit"},{role:"none"}]}]];
open();answer=false;get("portal-remove").onclick();assert.match(prompts.at(-1),/1, 2/);assert.equal(get("portal-side-0-role").value,"entry");
answer=true;get("portal-remove").onclick();assert.equal(get("portal-side-0-role").value,"unconfigured");assert.equal(walls[0][6].sides[0].role,"entry");
get("portal-form").onsubmit({preventDefault(){}});assert.equal(walls[0][6].sides[0].role,"unconfigured");assert.equal(walls[1][6].sides[0].role,"unconfigured");
assert.equal(get("portal-dialog").open,true);
console.log("Portal clean/dirty Close and Escape, Apply checkpoint, preserved applied edits and staged paired Reset confirmation passed");
