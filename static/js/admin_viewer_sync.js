// Manager-only read-only diagnostics; never render server strings as HTML.
(function () {
  "use strict";
  document.querySelectorAll("[data-viewer-sync]").forEach(panel => {
    const cid=panel.dataset.viewerSync, summary=panel.querySelector("[data-sync-summary]"), list=panel.querySelector("[data-sync-list]");
    const labels={connected:"Connected — awaiting display report",loading:"Loading", "up-to-date":"Up to date",failed:"Display failed",reconnecting:"Disconnected / reconnecting"};
    let stopped=false, timer;
    async function poll() {
      if (stopped) return;
      try {
        const response=await fetch(`/api/campaigns/${encodeURIComponent(cid)}/viewer-status`,{credentials:"same-origin",cache:"no-store",headers:{Accept:"application/json"}});
        if (!response.ok) {if ([401,403,404].includes(response.status)) stopped=true; throw new Error("Status unavailable");}
        const data=await response.json();
        summary.textContent=data.viewers.length ? `${data.viewers.length} display connection(s)${data.blank ? " — waiting screen" : ""}` : "No recent viewer connections";
        list.replaceChildren();
        data.viewers.forEach(row => {
          const li=document.createElement("li");
          li.textContent=`${row.username} · ${row.id}: ${labels[row.status] || "Unknown"} (last contact ${row.last_report_seconds}s ago)`;
          list.appendChild(li);
        });
      } catch (_) {
        summary.textContent="Viewer status unavailable — shown reports may be stale";
        list.replaceChildren();
      } finally {if (!stopped) timer=setTimeout(poll,5000);}
    }
    window.addEventListener("pagehide",()=>{stopped=true;clearTimeout(timer);});
    poll();
  });
})();
