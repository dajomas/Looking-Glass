// DM-only notes. All rendered HTML comes from the server's sanitized Markdown renderer.
window.LGRoomNotes = class {
  constructor(mapId, toast) {
    this.importSelecting=false;
    this.libraryEntries=[];this.libraryGeneration=0;
    this.editMode=false;this.saving=false;this.draftVersion=0;
    this.mapId=mapId;this.toast=toast;this.point=null;this.room=null;this.dirty=false;this.generation=0;this.revealed=null;this.stateStamp=null;this.refreshGeneration=0;
    this.$=id=>document.getElementById(id);
    this.nameOverlay=window.LGRoomNameOverlay?new window.LGRoomNameOverlay(mapId,toast):null;
    this.marker=window.LGRoomEditMarker?new window.LGRoomEditMarker(mapId,toast):null;
    this.libraryManager=window.LGRoomLibraryManager?new window.LGRoomLibraryManager(this):null;
    this.$("room-library-import").open=false;
    this.$("room-toggle").onclick=()=>this.collapse(!this.$("room-panel").classList.contains("collapsed"));
    try {this.collapse(localStorage.getItem("lg:room-panel-collapsed")==="true");} catch(_) {}
    for(const id of ["room-name","room-markdown"]) this.$(id).oninput=()=>{this.updateDirty();this.draftVersion++;};
    this.$("room-edit").onclick=()=>{if(this.room&&!this.saving){this.setEditMode(true);this.$("room-name").focus();}};
    this.$("room-cancel").onclick=()=>{if(!this.saving){this.dirty=false;if(this.room)this.show(this.room);}};
    this.$("room-clear").onclick=()=>{
      if(!this.room||!this.editMode||this.saving)return;
      this.$("room-name").value="";this.$("room-markdown").value="";
      this.updateDirty();this.draftVersion++;this.$("room-name").focus();
      this.toast("Name and notes cleared in draft. Save room to apply, or Cancel to restore.");
    };
    this.$("room-format-bar").onclick=e=>{
      const button=e.target.closest("[data-room-format]");
      if(button)this.format(button.dataset.roomFormat);
    };
    this.$("room-markdown").addEventListener("paste",e=>{
      if(!this.editMode||this.saving||!e.clipboardData)return;
      const types=Array.from(e.clipboardData.types||[]);
      const mime=types.includes("text/markdown")?"text/markdown":types.includes("text/plain")?"text/plain":null;
      if(mime){e.preventDefault();const text=e.clipboardData.getData(mime);this.insert(text,text.length,0);}
    });
    this.$("room-paste").onclick=async()=>{
      if(!this.editMode||this.saving)return;
      const generation=this.generation,version=this.draftVersion;
      try {
        if(!navigator.clipboard?.readText)throw new Error("Clipboard unavailable");
        const text=await navigator.clipboard.readText();
        if(!this.editMode||this.saving||generation!==this.generation||version!==this.draftVersion)return;
        this.insert(text,text.length,0);
      } catch(_) {this.$("room-markdown").focus();this.toast("Use Ctrl+V / ⌘V in the notes field to paste Markdown.","info");}
    };
    this.$("room-import-form").onsubmit=async e=>{
      e.preventDefault();
      const file=this.$("room-import-file").files[0];if(!file)return;
      const button=this.$("room-import-submit");if(button.disabled)return;
      if(file.size>1048576){this.toast("Markdown import exceeds 1 MiB.","error");return;}
      button.disabled=true;
      const importForm=this.$("room-import-form");
      const oldLabel=button.textContent;
      button.textContent="Importing…";
      importForm.setAttribute("aria-busy","true");
      this.$("room-import-status").textContent="Uploading and importing notes… Please wait.";
      const generation=++this.libraryGeneration;
      try {
        const body=new FormData();body.append("file",file);
        const result=await LGApi.post(`/api/maps/${this.mapId}/room-note-library/import`,body);
        if(generation!==this.libraryGeneration)return;
        this.libraryEntries=result.entries||[];this.renderLibrary();
        this.$("room-import-status").textContent=`${result.sections} sections at H${result.heading_level}; ${result.added} new entries.`+
          (result.ignored_preamble?" Text before the first room heading was ignored.":"");
        this.$("room-import-file").value="";
      } catch(error){this.$("room-import-status").textContent=error.message;this.toast(error.message,"error");}
      finally {button.disabled=false;button.textContent=oldLabel;importForm.removeAttribute("aria-busy");}
    };
    this.$("room-import-select").onchange=()=>{
      const select=this.$("room-import-select"),id=select.value;
      select.value=""; // Consume this action before rendering or opening a modal.
      if(!this.room||!this.editMode||this.saving||this.importSelecting)return;
      const entry=this.libraryEntries.find(e=>String(e.id)===id&&!e.assigned);
      if(!entry)return;
      this.importSelecting=true;
      try {
        const same=this.sameContent(this.$("room-name").value,this.$("room-markdown").value,entry.name,entry.markdown);
        if(this.hasUnsavedChanges()&&!same&&!confirm("Replace unsaved room name and notes with the imported entry?"))return;
        if(same)return;
        this.setEditMode(true);
        this.$("room-name").value=entry.name;this.$("room-markdown").value=entry.markdown;
        this.updateDirty();this.draftVersion++;this.$("room-name").focus();
      } finally {this.importSelecting=false;}
    };
    this.loadLibrary();
    this.setEditMode(false);
    this.$("room-form").onsubmit=async e=>{
      e.preventDefault();if(!this.room||!this.point||!this.editMode||this.saving)return;
      this.saving=true;
      this.$("room-form").querySelectorAll("input,textarea,select,button").forEach(el=>el.disabled=true);
      try {
        const room=await LGApi.post(`/api/maps/${this.mapId}/room-notes`,{
          ...this.point,area_key:this.room.area_key,revision:this.room.revision,
          name:this.$("room-name").value,markdown:this.$("room-markdown").value});
        this.dirty=false;this.show(room);this.toast("Room saved");
        await this.loadLibrary();
        this.nameOverlay?.refresh();
      } catch(error) {this.toast(error.message,"error");}
      finally {
        this.saving=false;
        this.$("room-form").querySelectorAll("input,textarea,select,button").forEach(el=>el.disabled=false);
        this.renderLibrary();
      }
    };
    window.addEventListener("beforeunload",e=>{if(this.hasUnsavedChanges()){e.preventDefault();e.returnValue="";}});
  }
  sameContent(name,markdown,otherName,otherMarkdown) {
    const text=value=>(value||"").replace(/\r\n?/g,"\n");
    return text(name).trim()===text(otherName).trim()&&text(markdown)===text(otherMarkdown);
  }
  updateDirty() {
    this.dirty=Boolean(this.room&&this.editMode&&!this.sameContent(
      this.$("room-name").value,this.$("room-markdown").value,this.room.name,this.room.markdown));
    return this.dirty;
  }
  hasUnsavedChanges() {return this.updateDirty();}
  renderLibrary() {
    const select=this.$("room-import-select");select.replaceChildren();
    const placeholder=document.createElement("option");placeholder.value="";
    const available=this.libraryEntries.filter(entry=>!entry.assigned);
    placeholder.textContent=available.length?"Choose imported room…":this.libraryEntries.length?"All imported room names are assigned":"No imported notes yet";select.appendChild(placeholder);
    const counts=new Map();for(const e of available)counts.set(e.name,(counts.get(e.name)||0)+1);
    for(const entry of available){
      const option=document.createElement("option");option.value=String(entry.id);
      option.textContent=entry.name+(counts.get(entry.name)>1?` (#${entry.id})`:"");select.appendChild(option);
    }
    this.$("room-import-choice").hidden=!this.room||!this.editMode;
    select.disabled=this.saving||!available.length;
  }
  async loadLibrary() {
    const generation=++this.libraryGeneration;
    try {
      const result=await LGApi.get(`/api/maps/${this.mapId}/room-note-library`);
      if(generation!==this.libraryGeneration)return;
      this.libraryEntries=result.entries||[];this.renderLibrary();
    } catch(error){this.toast("Room note library: "+error.message,"error");}
  }
  async refresh(state) {
    this.marker?.mapChanged(state);
    this.nameOverlay?.mapChanged(state);
    const stamp=`${state.cache_token}:${state.walls_version}:${state.fog_version}`;
    if(stamp===this.stateStamp)return;
    this.stateStamp=stamp;
    const generation=++this.refreshGeneration;
    try {
      const result=await LGApi.get(`/api/maps/${this.mapId}/room-notes`);
      if(generation!==this.refreshGeneration)return;
      const revealed=new Set(result.rooms.filter(r=>r.revealed).map(r=>r.area_key));
      const next=this.revealed && result.rooms.find(r=>r.revealed&&!this.revealed.has(r.area_key));
      this.revealed=revealed;
      if(next&&!this.hasUnsavedChanges()&&!this.editMode&&!this.editing()) await this.select(next.x,next.y);
      else if(this.room&&!this.hasUnsavedChanges()&&!this.editMode&&!this.editing()&&!revealed.has(this.room.area_key)) {
        this.$("room-preview").textContent="";this.$("room-title").textContent="";
        this.$("room-form").hidden=true;this.$("room-status").textContent="Room hidden or geometry changed.";
        this.room=null;this.point=null;this.setEditMode(false);
      }
    } catch(error) {this.stateStamp=null;this.toast(error.message,"error");}
  }
  setEditMode(value) {
    const opening=Boolean(value&&this.room&&!this.editMode);
    this.draftVersion++;
    this.editMode=Boolean(value&&this.room);
    this.$("room-read").hidden=!this.room||this.editMode;
    this.$("room-form").hidden=!this.editMode;
    this.$("room-status").hidden=this.editMode;
    this.$("room-library-import").hidden=this.editMode;
    this.renderLibrary();
    this.$("room-select-mode").closest("label").hidden=false;
    this.marker?.set(this.editMode,this.room,this.point);
    if(opening)this.loadLibrary();
  }
  insert(text, selectStart=0, selectLength=text.length) {
    if(!this.editMode||this.saving)return;
    const field=this.$("room-markdown"),start=field.selectionStart,end=field.selectionEnd;
    if(field.value.length-(end-start)+text.length>field.maxLength){
      this.toast("Room notes cannot exceed 100,000 characters.","warn");return;
    }
    field.setRangeText(text,start,end,"end");
    field.focus();field.setSelectionRange(start+selectStart,start+selectStart+selectLength);
    this.updateDirty();this.draftVersion++;
  }
  format(action) {
    if(!this.editMode||this.saving)return;
    const field=this.$("room-markdown"),start=field.selectionStart,end=field.selectionEnd;
    const selected=field.value.slice(start,end);
    const pairs={bold:["**","**"],italic:["*","*"],strike:["~~","~~"],code:["`","`"],link:["[","](https://example.com)"]};
    if(pairs[action]){
      const [before,after]=pairs[action],text=selected||"text";
      this.insert(before+text+after,before.length,text.length);return;
    }
    if(action==="fence"){
      const text=selected||"code";
      const ticks="`".repeat(Math.max(3,...Array.from(text.matchAll(/`+/g),m=>m[0].length+1)));
      const before=(start&&field.value[start-1]!=="\n"?"\n":"")+ticks+"\n";
      this.insert(before+text+"\n"+ticks+"\n",before.length,text.length);return;
    }
    if(action==="rule") {this.insert((start&&field.value[start-1]!=="\n"?"\n\n":"\n")+"---\n\n");return;}
    if(!["heading","bullet","number","quote"].includes(action))return;
    const lineStart=start===0?0:field.value.lastIndexOf("\n",start-1)+1;
    let lineEnd=field.value.indexOf("\n",end);
    if(end>start&&field.value[end-1]==="\n")lineEnd=end-1;
    if(lineEnd<0)lineEnd=field.value.length;
    const lines=field.value.slice(lineStart,lineEnd).split("\n");
    field.setSelectionRange(lineStart,lineEnd);
    this.insert(lines.map((line,i)=>(action==="heading"?"## ":action==="bullet"?"- ":action==="quote"?"> ":`${i+1}. `)+line).join("\n"));
  }
  editing() {return this.$("room-select-mode").checked;}
  collapse(value) {
    this.$("room-panel").classList.toggle("collapsed",value);
    document.querySelector("main.editor").classList.toggle("room-panel-collapsed",value);
    this.$("room-panel-body").hidden=value;
    this.$("room-toggle").setAttribute("aria-expanded",String(!value));
    try {localStorage.setItem("lg:room-panel-collapsed",String(value));} catch(_) {}
  }
  show(room) {
    this.room=room;this.dirty=false;
    this.$("room-title").textContent=room.name||"Unnamed room";
    this.$("room-name").value=room.name;
    this.$("room-markdown").value=room.markdown;
    this.$("room-preview").innerHTML=room.html;
    this.$("room-status").textContent=room.revealed ? "Revealed room · DM notes only" : "Hidden room · DM notes only";
    this.setEditMode(false);
  }
  async select(x,y,explicit=false) {
    if(this.saving)return;
    if(this.hasUnsavedChanges() && !confirm("Discard unsaved room notes?"))return;
    const generation=++this.generation;
    const room=await LGApi.post(`/api/maps/${this.mapId}/room-at`,{x,y});
    if(generation!==this.generation)return;
    if(!explicit && !room.revealed) {
      this.point=null;this.room=null;this.dirty=false;this.setEditMode(false);
      this.$("room-form").hidden=true;this.$("room-preview").textContent="";
      this.$("room-title").textContent="";this.$("room-status").textContent="Room hidden.";return;
    }
    this.point={x,y};this.dirty=false;this.show(room);
    if(explicit&&this.editing()&&!(room.name||"").trim()) {
      this.setEditMode(true);
      if(!this.$("room-panel-body").hidden)this.$("room-name").focus();
    }
    // A deliberate collapse stays collapsed; notes still update in the background.
  }
};
