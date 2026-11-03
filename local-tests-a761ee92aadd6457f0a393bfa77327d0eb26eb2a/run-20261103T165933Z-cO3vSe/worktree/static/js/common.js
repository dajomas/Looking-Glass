// Shared helpers for every page.
(function () {
  "use strict";
  // Confirm destructive form posts: <form data-confirm="Really?">
  document.addEventListener("submit", (ev) => {
    const msg = ev.target.getAttribute && ev.target.getAttribute("data-confirm");
    if (msg && !window.confirm(msg)) ev.preventDefault();
  });
  // Links to the viewer portal on the same host but the viewer port.
  document.querySelectorAll("[data-viewer-link]").forEach((a) => {
    const port = a.getAttribute("data-port");
    const path = a.getAttribute("data-path") || "/";
    a.href = `${location.protocol}//${location.hostname}:${port}${path}`;
  });
  // Auto-hide flash messages
  document.querySelectorAll(".flash-ok").forEach((el) => setTimeout(() => el.classList.add("fade"), 4000));
})();
