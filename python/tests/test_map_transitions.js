const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
class Element{
 constructor(id="",tag=""){Object.assign(this,{id,tagName:tag,value:"",checked:false,disabled:false,hidden:false,open:false,children:[],textContent:"",events:{}});}
 append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}
 setAttribute(k,v){this[k]=v;}showModal(){this.open=true;}close(){this.open=false;}
 addEventListener(k,fn){this.events[k]=fn;}click(){if(!this.disabled)return this.onclick?.();}
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));async function settle(){for(let i=0;i<8;i++)await tick();}
async function main(){
 const els=new Map(),get=id=>{if(!els.has(id))els.set(id,new Element(id));return els.get(id);};
 const html=fs.readFileSync("templates/partials/_map_transitions.html","utf8")+fs.readFileSync("web_html/admin/map_editor.html","utf8");
 for(const [,tag,id] of html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"/g))get(id).tagName=tag.toUpperCase();
 let row={id:"a",map_id:1,name:"Source",player_label:"Up",kind:"stairs",x:50,y:50,visibility:"secret",availability:"usable",arrival:"preserve",notes:"Notes",current_visibility:"secret",current_availability:"usable",destination_id:"b",revision:1,runtime_visibility:null,runtime_availability:null};
 let target={id:"b",map_id:2,name:"Target",kind:"stairs",x:70,y:70,revision:1};
 let fail=false,confirmAnswer=true,notified=0,tab=null,blocked=false,prompts=0;
 const posts=[],confirmations=[],events={},clone=x=>JSON.parse(JSON.stringify(x));
 const listing=()=>({ok:true,active_map_id:1,maps:[{id:1,name:"Ground",viewer_transition_markers:1,viewer_transition_labels:1},{id:2,name:"Upper"}],endpoints:[clone(row),target]});
 const c={console,URLSearchParams,setInterval(){},location:{href:"",search:""},confirm:msg=>{confirmations.push(msg);return confirmAnswer;},
 window:{addEventListener(k,fn){events[k]=fn;},LGChooseFog:async()=>{prompts++;throw Error("inspection must not prompt");},open(){if(blocked)return null;tab={opener:{},location:{href:"about:blank"},closed:false,close(){this.closed=true;}};return tab;},crypto:{randomUUID:()=>"request-123456"}},
 document:{getElementById:get,createElement:tag=>new Element("",tag),createElementNS:(ns,tag)=>new Element("",tag),querySelectorAll(){return [...els.values()].filter(e=>["BUTTON","INPUT","SELECT","TEXTAREA"].includes(e.tagName));}},
 LGApi:{get:async path=>path.endsWith("preview")?{source_revision:row.revision,destination_revision:1,destination_version:["t",0,1],destination_map_name:"Upper",destination_name:"Target",arrival:"preserve",needs_override:false,source_visibility:"secret",source_state:"usable"}:listing(),
 post:async(path,body)=>{
  posts.push({path,body});if(fail)throw Error("Server rejected stale state");
  if(path.endsWith("/travel"))return {admin_url:"/maps/2"};
  if(path.endsWith("/runtime")){assert.equal(body.revision,row.revision);row={...row,runtime_visibility:body.visibility,runtime_availability:body.availability,revision:row.revision+1};return listing();}
  if(path.endsWith("/transitions")){row={...row,...body,id:"created",revision:1,runtime_visibility:null,runtime_availability:null};return {...listing(),saved_endpoint_id:"created"};}
  assert.equal(body.revision,row.revision);const overrides={runtime_visibility:row.runtime_visibility,runtime_availability:row.runtime_availability};
  row={...row,...body,...overrides,name:body.name.trim(),revision:row.revision+1};return {...listing(),saved_endpoint_id:row.id};
 },del:async()=>listing()}};
 vm.createContext(c);vm.runInContext(fs.readFileSync("static/js/map_transitions.js","utf8"),c);
 const app=c.window.LGMapTransitions.mount({mapId:1,campaignId:9,scale:()=>1,dimensions:()=>({width:400,height:200}),onSaved:async()=>notified++,cancelGestures(){}});
 const dirty=()=>get("transition-form").events.input();
 const submit=async()=>{get("transition-form").onsubmit({preventDefault(){}});await settle();};
 await settle();app.tap(50,50,{button:0});
 get("tr-name").value=" Renamed ";get("tr-current-visibility").value="discovered";dirty();
 assert.match(get("tr-config-status").textContent,/Unsaved/);assert.match(get("tr-session-status").textContent,/Unsaved/);
 get("tr-save-runtime").click();await settle();
 assert.equal(row.name,"Source");assert.equal(row.runtime_visibility,"discovered");assert.equal(get("tr-name").value," Renamed ");
 assert.match(get("tr-config-status").textContent,/Unsaved/);assert.doesNotMatch(get("tr-session-status").textContent,/Unsaved/);assert.equal(get("transition-editor").open,true);
 // Configuration save must not send/overwrite unsaved session selections.
 get("tr-current-availability").value="blocked";dirty();await submit();
 assert.equal(row.name,"Renamed");assert.equal(row.runtime_availability,null);assert.equal(get("tr-current-availability").value,"blocked");
 assert.equal(posts.at(-1).body.revision,2);assert.equal("runtime_availability" in posts.at(-1).body,false);
 assert.doesNotMatch(get("tr-config-status").textContent,/Unsaved/);assert.match(get("tr-session-status").textContent,/Unsaved/);
 assert.equal(get("transition-editor").open,true);assert.equal(get("tr-name").value,"Renamed");
 // Close/Escape must preserve pending state when discard is declined.
 confirmAnswer=false;get("tr-close").click();assert.equal(get("transition-editor").open,true);
 let prevented=false;get("transition-editor").events.cancel({preventDefault(){prevented=true;}});assert.ok(prevented);assert.equal(get("transition-editor").open,true);
 get("tr-save-runtime").click();await settle();assert.equal(row.runtime_availability,"blocked");assert.equal(posts.at(-1).body.revision,3);
 // Valid session changes can save even while unrelated configuration fields are invalid.
 get("tr-name").value="";get("tr-current-visibility").value="secret";dirty();get("tr-save-runtime").click();await settle();assert.equal(get("tr-name").value,"");assert.equal(row.name,"Renamed");
 // Failed saves retain both drafts, baselines, revision and open dialog.
 fail=true;get("tr-current-availability").value="approval";get("tr-name").value="Pending name";dirty();const revision=row.revision;
 get("tr-save-runtime").click();await settle();assert.equal(row.revision,revision);assert.equal(get("tr-name").value,"Pending name");assert.equal(get("tr-current-availability").value,"approval");
 await submit();assert.equal(row.revision,revision);assert.equal(get("transition-editor").open,true);assert.match(get("transition-error").textContent,/stale/);assert.equal(get("tr-close").disabled,false);fail=false;
 // Read-only inspection keeps drafts and never activates the viewer.
 const count=posts.length,refreshes=notified;get("tr-open").click();await settle();assert.equal(posts.length,count);assert.equal(prompts,0);assert.equal(tab.location.href,"/maps/2");assert.equal(tab.opener,null);assert.equal(notified,refreshes);assert.equal(get("tr-name").value,"Pending name");
 // Travel warns about saved-state scope; declining sends no request.
 get("tr-travel").click();await settle();assert.equal(posts.length,count);assert.equal(get("transition-travel").open,false);
 confirmAnswer=true;get("tr-travel").click();await settle();assert.equal(get("transition-travel").open,true);
 get("transition-travel-form").onsubmit({preventDefault(){}});await settle();assert.equal(posts.at(-1).path,"/api/campaigns/9/travel");
 get("tr-cancel-travel").click();get("transition-add").click();app.tap(150,80,{button:0});get("tr-name").value="New endpoint";await submit();
 assert.equal(posts.at(-1).body.revision,null);assert.equal(get("transition-editor").open,true);assert.equal(get("tr-save-runtime").hidden,false);assert.equal(get("tr-delete").hidden,false);
 get("tr-current-availability").value="approval";dirty();get("tr-save-runtime").click();await settle();assert.equal(posts.at(-1).path,"/api/campaigns/9/transitions/created/runtime");assert.equal(posts.at(-1).body.revision,1);
 console.log("Save scopes, cross-group draft preservation, normalized configuration, revision chaining, errors, close/Escape, inspection and Travel warnings passed");
}
main().catch(e=>{console.error(e);process.exitCode=1;});
