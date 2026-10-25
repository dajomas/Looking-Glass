// Inspect all imported Markdown safely as text, and delete unassigned library entries.
window.LGRoomLibraryManager = class {
  constructor(owner) {
    this.owner=owner;this.mapId=owner.mapId;this.generation=0;this.busy=false;
    this.$=id=>document.getElementById(id);
    this.dialog=this.$("room-library-dialog");
    this.$("room-library-open").onclick=()=>{this.dialog.showModal();this.refresh();};
    this.$("room-library-close").onclick=()=>this.dialog.close();
    this.$("room-library-refresh").onclick=()=>this.refresh();
    this.dialog.addEventListener("close",()=>{this.generation++;this.busy=false;this.$("room-library-refresh").disabled=false;});
    this.$("room-library-list").onclick=e=>{
      const button=e.target.closest("[data-delete-room-import]");
      if(button)this.remove(Number(button.dataset.deleteRoomImport));
    };
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
      if(!entry.assigned){
        const button=add(card,"button","Delete imported entry","danger");
        button.type="button";button.dataset.deleteRoomImport=String(entry.id);
      }
    }
    this.status(entries.length?`${entries.length} imported entries · ${entries.filter(e=>e.assigned).length} assigned`:"No imported room notes.");
  }
  accept(entries) {
    ++this.owner.libraryGeneration;
    this.owner.libraryEntries=entries;this.owner.renderLibrary();this.render(entries);
  }
  async refresh() {
    if(this.busy)return;
    this.busy=true;const generation=++this.generation;this.status("Loading imported room notes…");
    this.$("room-library-refresh").disabled=true;
    try {
      const result=await LGApi.get(`/api/maps/${this.mapId}/room-note-library`);
      if(generation===this.generation)this.accept(result.entries||[]);
    } catch(error){if(generation===this.generation)this.status(error.message);}
    finally {if(generation===this.generation){this.busy=false;this.$("room-library-refresh").disabled=false;}}
  }
  async remove(id) {
    const entry=this.entries?.find(e=>e.id===id);
    if(this.busy||!entry||entry.assigned)return;
    if(!confirm(`Delete imported entry "${entry.name}"? This cannot be undone. Saved map rooms will not be deleted.`))return;
    this.busy=true;const generation=++this.generation;
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
        this.busy=false;
        this.$("room-library-list").querySelectorAll("button").forEach(b=>b.disabled=false);
      }
    }
  }
};
