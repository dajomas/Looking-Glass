const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
class Element{
 constructor(id="",tag=""){Object.assign(this,{id,tagName:tag,value:"",checked:false,disabled:false,hidden:false,open:false,children:[],textContent:""});}
 append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}
 setAttribute(k,v){this[k]=v;}showModal(){this.open=true;}close(){this.open=false;}click(){if(!this.disabled)return this.onclick?.();}
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));async function settle(){for(let i=0;i<6;i++)await tick();}
async function main(){
 const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);};
 const html=fs.readFileSync("templates/partials/_map_transitions.html","utf8")+fs.readFileSync("web_html/admin/map_editor.html","utf8");
 for(const [,tag,id] of html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"/g))get(id).tagName=tag.toUpperCase();
 const posts=[];let fail=false,failRead=false,notified=0,cancelled=0,choice="restore",tab=null,popupBlocked=false;const choices=[];
 let data={active_map_id:1,maps:[{id:1,name:"Ground",viewer_transition_markers:1,viewer_transition_labels:1},{id:2,name:"Upper"}],endpoints:[
 {id:"a",map_id:1,name:"Source",player_label:"Up",kind:"stairs",x:50,y:50,visibility:"discovered",availability:"usable",arrival:"preserve",notes:"Notes",current_visibility:"discovered",current_availability:"usable",destination_id:"b",revision:1},
 {id:"b",map_id:2,name:"Target",kind:"stairs",x:70,y:70,destination_id:null,revision:1}]};
 const clone=x=>JSON.parse(JSON.stringify(x)),preview={source_revision:1,destination_revision:1,destination_version:["token",0,1],destination_map_name:"Upper",destination_name:"Target",arrival:"preserve",needs_override:false,source_visibility:"discovered",source_state:"usable",warning:false};
 const ctx={console,URLSearchParams,setInterval(){},location:{search:"",href:""},window:{addEventListener(){},LGChooseFog:async(...args)=>{choices.push(args);return choice;},open(){if(popupBlocked)return null;tab={closed:false,opener:{},location:{href:"about:blank"},close(){this.closed=true;}};return tab;},crypto:{randomUUID:()=>"request-123456"}},confirm:()=>true,
 document:{getElementById:get,createElement:tag=>new Element("",tag),createElementNS:(ns,tag)=>new Element("",tag),querySelectorAll(){return [...elements.values()].filter(x=>x.tagName==="BUTTON");}},
 LGApi:{get:async path=>{if(failRead)throw Error("Cannot inspect destination");return clone(path.endsWith("preview")?preview:data);},post:async(path,body)=>{posts.push({path,body});if(fail)throw Error("Server rejected stale state");if(path.endsWith("/travel"))return {admin_url:"/maps/2"};if(path.endsWith("/transitions/a"))data.endpoints[0]={...data.endpoints[0],...body,revision:2};return clone(data);},del:async()=>clone(data)}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync("static/js/map_transitions.js","utf8"),ctx);
 const app=ctx.window.LGMapTransitions.mount({mapId:1,campaignId:9,scale:()=>1,dimensions:()=>({width:400,height:200}),onSaved:async()=>notified++,cancelGestures:()=>cancelled++});
 await settle();assert.equal(get("transition-list").children.length,1);
 assert.equal(app.tap(50,50,{button:0}),true);assert.equal(get("transition-editor").open,true);assert.equal(get("tr-name").value,"Source");
 get("tr-name").value="Renamed";get("tr-place").click();assert.equal(get("transition-editor").open,false);
 app.tap(90,100,{button:0});assert.equal(get("tr-name").value,"Renamed");assert.equal(Number(get("tr-x").value),90);
 get("transition-form").onsubmit({preventDefault(){}});await settle();assert.equal(posts.at(-1).body.name,"Renamed");assert.equal(posts.at(-1).body.x,90);assert.equal(notified,1);
 assert.equal(get("transition-editor").open,false);assert.equal(app.tap(90,100,{button:2}),false);
 app.tap(90,100,{button:0});
 // Inspect must never ask a reveal question, mutate server state or refresh fog.
 const count=posts.length,oldNotified=notified;
 get("tr-name").value="Unsaved source draft";
 get("tr-open").click();await settle();
 assert.equal(posts.length,count);assert.equal(choices.length,0);assert.equal(notified,oldNotified);
 assert.equal(data.active_map_id,1);assert.equal(tab.location.href,"/maps/2");assert.equal(tab.opener,null);
 assert.equal(ctx.location.href,"");assert.equal(get("transition-editor").open,true);assert.equal(get("tr-name").value,"Unsaved source draft");
 popupBlocked=true;get("tr-open").click();await settle();assert.equal(ctx.location.href,"/maps/2");assert.equal(posts.length,count);assert.equal(choices.length,0);popupBlocked=false;ctx.location.href="";
 failRead=true;get("tr-open").click();await settle();assert.equal(tab.closed,true);assert.equal(ctx.location.href,"");assert.equal(posts.length,count);assert.equal(get("tr-open").disabled,false);failRead=false;
 // A changed saved destination must not silently inspect a new route.
 data.endpoints[0].revision++;get("tr-open").click();await settle();assert.equal(tab.closed,true);assert.equal(posts.length,count);assert.match(get("transition-error").textContent,/changed/);
 app.tap(90,100,{button:0});get("tr-travel").click();await settle();assert.equal(get("transition-travel").open,true);
 get("transition-travel-form").onsubmit({preventDefault(){}});await settle();assert.equal(ctx.location.href,"/maps/2");assert.equal(posts.at(-1).body.source_endpoint_id,"a");
 get("tr-cancel-travel").click();get("transition-add").click();app.tap(150,80,{button:0});get("tr-name").value="New ladder";get("tr-place").click();app.tap(160,90,{button:0});assert.equal(get("tr-name").value,"New ladder");
 fail=true;get("transition-form").onsubmit({preventDefault(){}});await settle();assert.equal(get("transition-editor").open,true);assert.match(get("transition-error").textContent,/stale/);assert.equal(get("tr-close").disabled,false);assert.ok(cancelled>0);
 console.log("Map passage UI: selection, non-destructive placement, save, explicit travel, busy cleanup and error retention passed");
}
main().catch(e=>{console.error(e);process.exitCode=1;});
