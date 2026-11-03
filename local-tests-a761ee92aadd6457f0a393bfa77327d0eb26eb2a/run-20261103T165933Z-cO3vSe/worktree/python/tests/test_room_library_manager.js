const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Node {
 constructor(){this.children=[];this.dataset={};this.textContent='';this.disabled=false;this.events={};}
 appendChild(n){this.children.push(n);}
 replaceChildren(){this.children=[];}
 addEventListener(k,fn){this.events[k]=fn;}
 querySelectorAll(tag){return this.children.flatMap(c=>[...(tag==='button'&&c.tag==='button'?[c]:[]),...c.querySelectorAll(tag)]);}
 showModal(){this.open=true;}
 close(){this.open=false;this.events.close?.();}
}
const nodes=new Map(),node=id=>{if(!nodes.has(id))nodes.set(id,new Node());return nodes.get(id);};
let entries=[{id:1,name:'Taken',markdown:'Old',assigned:true,notes_match:false},{id:2,name:'<unsafe>',markdown:'<script>bad</script>',assigned:false}],calls=0,answer=true,reject=false;
const c={window:{},document:{getElementById:node,createElement:tag=>Object.assign(new Node(),{tag})},confirm:()=>answer,
 LGApi:{get:async()=>({entries}),del:async()=>{calls++;if(reject)throw Error('Now assigned');entries=entries.filter(e=>e.id!==2);return {entries};}}};
vm.runInNewContext(fs.readFileSync('static/js/room_library_manager.js','utf8'),c);
(async()=>{
 const owner={mapId:1,libraryGeneration:0,renderLibrary(){this.renders=(this.renders||0)+1;}};
 const manager=new c.window.LGRoomLibraryManager(owner);await manager.refresh();
 const list=node('room-library-list');assert.equal(list.children.length,2);assert.equal(list.querySelectorAll('button').length,2);
 assert.equal(list.children[1].children[0].textContent,'<unsafe> (#2)');
 assert.equal(list.children[1].children[2].children[1].textContent,'<script>bad</script>','notes must be assigned via textContent');
 await manager.remove(1);assert.equal(calls,0,'assigned entry has no delete action');
 answer=false;await manager.remove(2);assert.equal(calls,0);
 answer=true;reject=true;await manager.remove(2);assert.equal(node('room-library-status').textContent,'Now assigned');assert.equal(owner.libraryEntries.length,2);
 reject=false;await manager.remove(2);assert.equal(owner.libraryEntries.length,1);assert.equal(list.children.length,1);
 assert.equal(list.querySelectorAll('button').length,1);
 let posts=0,dirty=true;owner.hasUnsavedChanges=()=>dirty;
 c.LGApi.post=async(url)=>{
   posts++;assert.ok(url.endsWith('/1/unassign'));
   entries=entries.map(e=>({...e,assigned:false}));return {entries,unassigned:1,area_keys:['k']};
 };
 await manager.unassign(1);assert.equal(posts,0,'dirty drafts block unassign');
 dirty=false;answer=false;await manager.unassign(1);assert.equal(posts,0,'cancel does not mutate');
 answer=true;await manager.unassign(1);assert.equal(posts,1);
 assert.equal(owner.libraryEntries[0].assigned,false);assert.equal(manager.busy,false);
 assert.equal(node('room-library-close').disabled,false);
 assert.equal(list.querySelectorAll('button')[0].dataset.deleteRoomImport,'1');
 entries=entries.map(e=>({...e,assigned:true}));manager.accept(entries);
 owner.room={area_key:'k'};owner.point={x:10,y:10};owner.generation=0;
 let shown=0,overlay=0;owner.show=room=>{shown++;assert.equal(room.name,'');};
 owner.nameOverlay={refresh(){overlay++;}};
 c.LGApi.post=async(url)=>url.endsWith('/room-at')?{name:'',markdown:'',revision:2}:
   {entries:entries.map(e=>({...e,assigned:false})),unassigned:1,area_keys:['k']};
 await manager.unassign(1);assert.equal(shown,1);assert.equal(overlay,1);assert.equal(owner.generation,1);
 entries=entries.map(e=>({...e,assigned:true}));manager.accept(entries);
 c.LGApi.post=async()=>{throw Error('Permission denied');};
 await manager.unassign(1);assert.equal(node('room-library-status').textContent,'Permission denied');
 assert.equal(manager.busy,false);assert.equal(node('room-library-close').disabled,false);
 console.log('Library rendering, safe text, delete protection, unassign confirmation/draft guard, selected-room refresh and error recovery passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
