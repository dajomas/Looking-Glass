// Retain valid choices through list refreshes, Apply and reloads; never select a missing option.
(function () {
  "use strict";
  function key(select) {
    if (select.id === "room-import-select") return null; // one-shot action; never restore/replay it
    if (select.id === "map-switch") return null; // the URL/server is authoritative for this switch
    const row = select.closest("tr[data-map-id]");
    let name = select.id || select.name;
    let context = "";
    if (row) {
      const selects = [...row.querySelectorAll("select")];
      const index = selects.indexOf(select);
      name = `map:${row.dataset.mapId}:select:${index}`;
      if (index === 1) context = selects[0].value;
    } else if (select.id === "saved-scene") context = document.getElementById("saved-source")?.value || "";
    return name ? `lg:select:${location.pathname}:${name}:${context}` : null;
  }
  function read(k) {try {return localStorage.getItem(k);} catch (_) {return null;}}
  document.addEventListener("change", event => {
    const select = event.target;
    if (!(select instanceof HTMLSelectElement)) return;
    const k = key(select);
    if (k) {try {localStorage.setItem(k,select.value);} catch (_) {}}
  },true);
  let scheduled = false;
  function restore() {
    scheduled=false;
    for (const select of document.querySelectorAll("select")) {
      if (select.disabled || select.value !== "") continue;
      const k=key(select), stored=k ? read(k) : null;
      if (!stored || ![...select.options].some(o=>o.value===stored)) continue;
      select.value=stored;
      select.dispatchEvent(new Event("change",{bubbles:true}));
    }
  }
  function schedule() {if (!scheduled) {scheduled=true;queueMicrotask(restore);}}
  new MutationObserver(schedule).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:["disabled"]});
  schedule();
})();
