const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
class El{
 constructor(){Object.assign(this,{value:"",checked:false,disabled:false,hidden:false,open:false,children:[],events:{},textContent:"",scrollTop:0});}
 append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}
 setAttribute(k,v){this[k]=v;}addEventListener(k,fn){this.events[k]=fn;}showModal(){this.open=true;}close(){this.open=false;}focus(){}
}
const tick=()=>new Promise(r=>setImmediate(r));async function settle(){for(let i=0;i<6;i++)await tick();}
async function main(){
 const els=new Map(),get=id=>{if(!els.has(id))els.set(id,new El());return els.get(id);};
 const row={id:"a",map_id:1,name:"Source",player_label:"",kind:"stairs",x:50,y:50,visibility:"discovered",availability:"usable",arrival:"preserve",notes:"",destination_id:"b",revision:1};
 const listing={active_map_id:1,maps:[{id:1,name:"Source"},{id:2,name:"Upper"}],endpoints:[row,{id:"b",map_id:2,name:"Target",revision:1}]};
 let preview={},posts=[];
 const c={console,URLSearchParams,setInterval(){},confirm:()=>true,location:{search:"",href:""},window:{addEventListener(){},crypto:{randomUUID:()=>"request-12345"}},
 document:{getElementById:get,querySelectorAll:()=>[],createElement:()=>new El(),createElementNS:()=>new El()},
 LGApi:{get:async path=>path.endsWith("preview")?preview:listing,post:async(path,body)=>{posts.push({path,body});return {admin_url:"/maps/2"};}}};
 vm.createContext(c);vm.runInContext(fs.readFileSync("static/js/map_transitions.js","utf8"),c);
 const api=c.window.LGMapTransitions;
 let cases=0;
 for(const visibility of ["discovered","secret","admin"])for(const state of ["usable","blocked","approval"]){
  const p=api.approvalPresentation({source_visibility:visibility,source_state:state,needs_override:visibility==="secret"||state!=="usable"});
  assert.equal(p.needed,visibility==="secret"||state!=="usable");
  if(visibility==="secret"||state==="blocked")assert.equal(p.label,"Allow this trip despite passage restrictions");
  else if(state==="approval")assert.equal(p.label,"I approve this trip");
  else assert.equal(p.label,"");
  if(visibility==="secret")assert.match(p.help,/Secret passage/);
  if(state==="blocked")assert.match(p.help,/Blocked passage/);
  if(state==="approval")assert.match(p.help,/DM approval required/);
  cases++;
 }
 api.mount({mapId:1,campaignId:9,scale:()=>1,dimensions:()=>({width:400,height:200}),cancelGestures(){},onSaved:async()=>{}});
 await settle();get("transition-list").children[0].onclick();
 for(const [visibility,state,label] of [["secret","approval","Allow this trip despite passage restrictions"],["discovered","approval","I approve this trip"],["discovered","usable",""]]){
  preview={source_visibility:visibility,source_state:state,needs_override:visibility==="secret"||state!=="usable",destination_map_name:"Upper",destination_name:"Target",arrival:"preserve",source_revision:1,destination_revision:1,destination_version:["t",0,1]};
  await get("tr-travel").onclick();await settle();
  const needed=label!=="";
  assert.equal(get("tr-approval-control").hidden,!needed);assert.equal(get("tr-approve").required,needed);assert.equal(get("tr-approve").disabled,!needed);
  assert.equal(get("tr-approve").checked,false);assert.equal(get("tr-approval-label").textContent,label);
  get("tr-approve").checked=true;
  if(needed){get("tr-cancel-travel").onclick();assert.equal(posts.length,0);}
  else{get("transition-travel-form").onsubmit({preventDefault(){}});await settle();assert.equal(posts.at(-1).body.override,false);}
 }
 console.log(`${cases} state combinations, reason text, hidden/required/disabled state, checkbox reset, return flow and false override when not needed passed`);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
