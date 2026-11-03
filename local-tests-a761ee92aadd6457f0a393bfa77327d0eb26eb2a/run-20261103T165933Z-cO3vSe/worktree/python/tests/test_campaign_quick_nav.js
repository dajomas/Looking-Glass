const assert=require("node:assert/strict");
const fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
class Element {
 constructor(tag="DIV"){this.tagName=tag;this.listeners={};this.children=[];this.value="";this.dataset={};this.open=false;this.textContent="";}
 addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
 trigger(type,extra={}){const e={target:this,key:"",preventDefault(){this.defaultPrevented=true;},...extra};for(const f of this.listeners[type]||[])f(e);return e;}
 append(...elements){this.children.push(...elements);}
 replaceChildren(){this.children=[];}
 focus(){doc.activeElement=this;}
 select(){}
 showModal(){this.open=true;}
 close(){this.open=false;this.trigger("close");}
 click(){this.clicked=true;this.trigger("click");}
 querySelector(){return closeButton;}
 querySelectorAll(){return this.children.flatMap(c=>c.children.filter(e=>e.tagName==="A"));}
}
const dialog=new Element(),input=new Element("INPUT"),kind=new Element("SELECT"),list=new Element(),status=new Element(),opener=new Element("A"),closeButton=new Element("BUTTON");
dialog.dataset.campaignId="7";kind.value="all";
const ids={"campaign-quick-nav":dialog,"quick-nav-query":input,"quick-nav-kind":kind,"quick-nav-results":list,"quick-nav-status":status};
const doc=new Element();doc.activeElement=opener;doc.getElementById=id=>ids[id];doc.createElement=tag=>new Element(tag.toUpperCase());doc.querySelector=selector=>selector==="[data-quick-nav-open]"?opener:(dialog.open?dialog:null);
let pendingTimer=null;const requests=[];
const context={document:doc,AbortController,URLSearchParams,Error,setTimeout(fn){pendingTimer=fn;return 1;},clearTimeout(){pendingTimer=null;},fetch(url,options){return new Promise(resolve=>requests.push({url,options,resolve}));}};
vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,"../../static/js/campaign_quick_nav.js"),"utf8"),context);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const flush=()=>{const fn=pendingTimer;pendingTimer=null;fn?.();};
(async()=>{
 opener.trigger("click");assert(dialog.open);assert.equal(doc.activeElement,input);
 input.value="first";input.trigger("input");flush();assert.equal(requests.length,1);
 input.value="second";input.trigger("input");assert(requests[0].options.signal.aborted);flush();
 requests[1].resolve({ok:true,json:async()=>({results:[{title:"<script>",map_name:"Map",kind:"room",snippet:"Secret",url:"/campaigns/7/inspect/maps/1"}],truncated:false})});await tick();
 assert.equal(list.children.length,1);assert.equal(list.children[0].children[0].textContent,"<script> — Map [room]");
 requests[0].resolve({ok:true,json:async()=>({results:[],truncated:false})});await tick();assert.equal(list.children.length,1);
 dialog.trigger("keydown",{key:"ArrowDown"});assert.equal(doc.activeElement,list.children[0].children[0]);
 input.focus();dialog.trigger("keydown",{key:"Enter"});assert(list.children[0].children[0].clicked);
 closeButton.trigger("click");assert(!dialog.open);assert.equal(doc.activeElement,opener);
 doc.trigger("keydown",{key:"k",ctrlKey:true,target:input});assert(!dialog.open);
 doc.trigger("keydown",{key:"k",ctrlKey:true,target:opener});assert(dialog.open);
 console.log("Quick navigation DOM-stub regression passed: debounce/abort, stale response, safe text, keyboard, focus restoration.");
})().catch(e=>{console.error(e);process.exitCode=1;});
