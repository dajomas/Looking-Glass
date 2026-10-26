(() => {
  "use strict";
  const dialog=document.getElementById("campaign-quick-nav");
  if(!dialog || typeof dialog.showModal!=="function") return;
  const input=document.getElementById("quick-nav-query"),kind=document.getElementById("quick-nav-kind"),
    list=document.getElementById("quick-nav-results"),status=document.getElementById("quick-nav-status"),
    opener=document.querySelector("[data-quick-nav-open]");
  let controller=null,timer=null,revision=0,previous=null;
  const links=()=>[...list.querySelectorAll("a")];
  function cancel(){clearTimeout(timer);revision++;if(controller)controller.abort();controller=null;}
  function close(){cancel();if(dialog.open)dialog.close();}
  function open(event){
    if(document.querySelector("dialog[open]") && !dialog.open)return;
    event.preventDefault();previous=document.activeElement;
    if(!dialog.open)dialog.showModal();input.focus();input.select();schedule();
  }
  async function search(){
    cancel();const current=revision,query=input.value.trim();list.replaceChildren();
    if(!query){status.textContent="Type to search this campaign.";return;}
    controller=new AbortController();status.textContent="Searching…";
    try{
      const url=`/api/campaigns/${dialog.dataset.campaignId}/search?`+new URLSearchParams({q:query,kind:kind.value});
      const response=await fetch(url,{signal:controller.signal,headers:{Accept:"application/json"},cache:"no-store"});
      if(!response.ok)throw Error("Search failed ("+response.status+"). Reload or use the full search page.");
      const data=await response.json();
      if(current!==revision || !dialog.open)return;
      for(const item of data.results){
        const li=document.createElement("li"),a=document.createElement("a"),p=document.createElement("p");
        a.href=item.url;a.textContent=`${item.title} — ${item.map_name} [${item.kind}]`;
        p.textContent=item.snippet;li.append(a,p);list.append(li);
      }
      status.textContent=data.results.length?`${data.results.length} results${data.truncated?" shown; refine your search for more matches":""}.`:"No matching results.";
    }catch(error){if(error.name!=="AbortError" && current===revision)status.textContent=error.message;}
  }
  function schedule(){cancel();list.replaceChildren();status.textContent=input.value.trim()?"Searching…":"Type to search this campaign.";timer=setTimeout(search,200);}
  opener.addEventListener("click",open);
  dialog.querySelector("[data-quick-nav-close]").addEventListener("click",close);
  input.addEventListener("input",schedule);kind.addEventListener("change",schedule);
  dialog.addEventListener("close",()=>{cancel();previous?.focus();});
  dialog.addEventListener("cancel",()=>cancel());
  dialog.addEventListener("keydown",event=>{
    const items=links(),index=items.indexOf(document.activeElement);
    if(event.key==="ArrowDown" && items.length && (document.activeElement===input || index>=0)){
      event.preventDefault();items[(index+1)%items.length].focus();
    }else if(event.key==="ArrowUp" && items.length && (document.activeElement===input || index>=0)){
      event.preventDefault();items[index<=0?items.length-1:index-1].focus();
    }else if(event.key==="Enter" && document.activeElement===input && items.length){event.preventDefault();items[0].click();}
  });
  document.addEventListener("keydown",event=>{
    if(event.defaultPrevented || event.repeat || event.isComposing || !(event.ctrlKey||event.metaKey) || event.altKey || event.shiftKey || event.key.toLowerCase()!=="k")return;
    if(!dialog.open && (event.target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName)))return;
    open(event);
  });
})();
