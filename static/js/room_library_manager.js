// Inspect imports safely, unassign saved room metadata, and delete unused entries.
window.LGRoomLibraryManager = class {
  constructor(owner) {
    this.owner=owner;this.mapId=owner.mapId;this.generation=0;this.busy=false;
    this.$=id=>document.getElementById(id);
    this.dialog=this.$("room-library-dialog");
    this.$("room-library-open").onclick=()=>{this.dialog.showModal();this.refresh();};
    this.$("room-library-close").onclick=()=>this.dialog.close();
    this.$("room-library-refresh").onclick=()=>this.refresh();
    this.dialog.addEventListener("cancel",e=>{if(this.busy)e.preventDefault();});
    this.dialog.addEventListener("close",()=>{this.generation++;this.setBusy(false);});
    this.$("room-library-list").onclick=e=>{
      const unassign=e.target.closest("[data-unassign-room-import]");
      if(unassign){this.unassign(Number(unassign.dataset.unassignRoomImport));return;}
      const button=e.target.closest("[data-delete-room-import]");
      if(button)this.remove(Number(button.dataset.deleteRoomImport));
    };
  }
  setBusy(value) {
    this.busy=value;
    for(const id of ["room-library-close","room-library-refresh"] )this.$(id).disabled=value;
    this.$("room-library-list").querySelectorAll("button").forEach(b=>b.disabled=value);
  }
  status(message) {this.$("room-library-status").textContent=message;}
  render(entries) {
    this.entries=entries;
    const list=this.$("room-library-list");list.replaceChildren();
    const add=(parent,tag,text,className)=>{
      const node=document.createElement(tag);node.textContent=text;
      if(className)node.className=className;parent.appendChild(node);return node;
    };
    for(const entry of entries){
      const card=add(list,"section","","room-library-entry");
      add(card,"h3",`${entry.name} (#${entry.id})`);
      add(card,"p",entry.assigned?(entry.notes_match?"Assigned · name and notes match":"Assigned · saved notes differ from this import"):"Unassigned",entry.assigned?"pill pill-live":"pill");
      const details=document.createElement("details");details.open=true;
      add(details,"summary","Markdown notes");add(details,"pre",entry.markdown||"(No notes)");card.appendChild(details);
      if(entry.assigned){
        const button=add(card,"button","Unassign from rooms","danger");
        button.type="button";button.dataset.unassignRoomImport=String(entry.id);
      } else {
        const button=add(card,"button","Delete imported entry","danger");
        button.type="button";button.dataset.deleteRoomImport=String(entry.id);
      }
    }
    this.status(entries.length?`${entries.length} imported entries · ${entries.filter(e=>e.assigned).length} assigned`:"No imported room notes.");
  }
  accept(entries) {
    ++this.owner.libraryGeneration;
    this.owner.libraryEntries=entries;this.owner.renderLibrary();
    const list=this.$("room-library-list"),scroll=list.scrollTop;
    this.render(entries);list.scrollTop=scroll;
    if(this.busy)this.setBusy(true);
  }
  async refresh() {
    if(this.busy)return;
    this.setBusy(true);const generation=++this.generation;this.status("Loading imported room notes…");
    this.$("room-library-refresh").disabled=true;
    try {
      const result=await LGApi.get(`/api/maps/${this.mapId}/room-note-library`);
      if(generation===this.generation)this.accept(result.entries||[]);
    } catch(error){if(generation===this.generation)this.status(error.message);}
    finally {if(generation===this.generation){this.setBusy(false);}}
  }
  async unassign(id) {
    const entry=this.entries?.find(e=>e.id===id);
    if(this.busy||!entry?.assigned)return;
    if(this.owner.saving||this.owner.hasUnsavedChanges?.()){
      this.status("Save or cancel the current room draft before unassigning.");return;
    }
    if(!confirm(`Unassign "${entry.name}" from ALL matching rooms in this map? Saved names and notes, including custom edits, will be cleared. The imported entry will be kept. This cannot be undone.`))return;
    this.setBusy(true);const generation=++this.generation;
    try {
      const result=await LGApi.post(`/api/maps/${this.mapId}/room-note-library/${id}/unassign`,{});
      if(generation!==this.generation)return;
      this.accept(result.entries||[]);
      const keys=new Set(result.area_keys||[]);
      if(this.owner.room&&keys.has(this.owner.room.area_key)){
        // Keep the selected area, but replace its saved metadata and revision.
        const room=await LGApi.post(`/api/maps/${this.mapId}/room-at`,this.owner.point);
        if(generation!==this.generation)return;
        ++this.owner.generation;this.owner.show(room);
      }
      this.owner.nameOverlay?.refresh();
      this.status(`${result.unassigned} room assignment(s) cleared. Imported entry retained.`);
    } catch(error){
      if(generation!==this.generation)return;
      try {const result=await LGApi.get(`/api/maps/${this.mapId}/room-note-library`);if(generation===this.generation)this.accept(result.entries||[]);} catch(_) {}
      if(generation===this.generation)this.status(error.message);
    } finally {if(generation===this.generation)this.setBusy(false);}
  }
  async remove(id) {
    const entry=this.entries?.find(e=>e.id===id);
    if(this.busy||!entry||entry.assigned)return;
    if(!confirm(`Delete imported entry "${entry.name}"? This cannot be undone. Saved map rooms will not be deleted.`))return;
    this.setBusy(true);const generation=++this.generation;
    this.$("room-library-list").querySelectorAll("button").forEach(b=>b.disabled=true);
    try {
      const result=await LGApi.del(`/api/maps/${this.mapId}/room-note-library/${id}`);
      if(generation===this.generation)this.accept(result.entries||[]);
    } catch(error){
      if(generation!==this.generation)return;
      // A different session may have assigned the name since the list was opened.
      try {const result=await LGApi.get(`/api/maps/${this.mapId}/room-note-library`);if(generation===this.generation)this.accept(result.entries||[]);} catch(_) {}
      if(generation===this.generation)this.status(error.message);
    } finally {
      if(generation===this.generation){
        this.setBusy(false);
      }
    }
  }
};
