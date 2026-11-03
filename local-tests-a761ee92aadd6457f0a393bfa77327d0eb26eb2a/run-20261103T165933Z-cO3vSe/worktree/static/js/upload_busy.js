/* Native file forms: preserve successful controls and block repeat submits. */
(function () {
  "use strict";
  const pending = new Map();
  function reset(form) {
    const state = pending.get(form); if (!state) return;
    for (const item of state.buttons) {
      item.el.innerHTML = item.html;
      if (item.aria === null) item.el.removeAttribute("aria-disabled");
      else item.el.setAttribute("aria-disabled", item.aria);
    }
    if (state.aria === null) form.removeAttribute("aria-busy");
    else form.setAttribute("aria-busy", state.aria);
    state.status.remove(); pending.delete(form);
  }
  document.addEventListener("submit", event => {
    if (pending.has(event.target)) {event.preventDefault();event.stopImmediatePropagation();}
  }, true);
  document.addEventListener("click", event => {
    const button = event.target.closest && event.target.closest('button,input[type="submit"],input[type="image"]');
    if (button && button.form && pending.has(button.form) &&
        (button.type === "submit" || button.type === "image")) {
      event.preventDefault(); event.stopImmediatePropagation();
    }
  }, true);
  document.addEventListener("submit", event => {
    const form = event.target;
    if (pending.has(form)) {event.preventDefault(); return;}
    // JS-managed upload forms prevent default and own their completion lifecycle.
    if (event.defaultPrevented || !form.querySelector || !form.querySelector('input[type="file"]')) return;
    const status = document.createElement("p");
    status.className = "upload-busy-status";
    status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
    status.textContent = "Uploading and processing files… Please wait. Do not submit again.";
    const buttons = [...form.querySelectorAll('button[type="submit"],button:not([type]),input[type="submit"]')]
      .map(el => ({el, html:el.innerHTML, aria:el.getAttribute("aria-disabled")}));
    pending.set(form, {buttons, status, aria:form.getAttribute("aria-busy")});
    form.setAttribute("aria-busy", "true");
    for (const item of buttons) {
      item.el.setAttribute("aria-disabled", "true");
      if (item.el.tagName === "BUTTON") item.el.textContent = "Processing…";
    }
    // Do not disable form controls: files, CSRF and named submitters must be sent.
    form.append(status);
  });
  window.addEventListener("pageshow", () => {for (const form of [...pending.keys()]) reset(form);});
})();
