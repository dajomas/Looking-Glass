// Query the target's current checkpoint before EVERY display/switch action.
(function () {
  "use strict";
  const dialog = document.getElementById("map-display-dialog");
  let pending = false;
  window.LGChooseFog = async function(name, mapId = window.LG_MAP?.id, options = {}) {
    if (!mapId) throw new Error("No target map selected.");
    if (pending) return null;
    pending = true;
    try {
      const response = await fetch(`/api/maps/${mapId}/display-options`, {
        credentials: "same-origin", cache: "no-store", headers: {Accept: "application/json"}});
      if (!response.ok) throw new Error("Cannot check saved reveals. No map was displayed.");
      const data = await response.json();
      if (!data.ok) throw new Error(data.error || "Cannot check saved reveals.");
      if (!data.can_restore && !(options.includeCurrentReveals && data.has_current_reveals)) return "reset";
      if (!dialog) throw new Error("Restore/reset dialog is missing.");
      document.getElementById("map-display-question").textContent = `Show "${name}" to players?`;
      dialog.returnValue = "cancel";
      return await new Promise(resolve => {
        dialog.addEventListener("close", () => resolve(
          ["restore", "reset"].includes(dialog.returnValue) ? dialog.returnValue : null), {once: true});
        dialog.showModal();
      });
    } finally {pending = false;}
  };
  document.querySelectorAll("form[data-map-display]").forEach(form => {
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const button = form.querySelector('button[type="submit"]');
      if (button?.disabled) return;
      if (button) button.disabled = true;
      try {
        const action = await window.LGChooseFog(form.dataset.mapName, Number(form.elements.map_id.value));
        if (!action) return;
        form.elements.fog_action.value = action;
        HTMLFormElement.prototype.submit.call(form);
      } catch (error) {
        let message = form.querySelector('[role="status"]');
        if (!message) {message = document.createElement("p"); message.setAttribute("role", "status"); form.append(message);}
        message.textContent = error.message;
      } finally {if (button) button.disabled = false;}
    });
  });
})();
