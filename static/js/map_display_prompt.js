// A mandatory, explicit reveal policy before either admin Show action.
(function () {
  "use strict";
  const dialog = document.getElementById("map-display-dialog");
  window.LGChooseFog = function (name) {
    return new Promise(resolve => {
      dialog.returnValue = "cancel";
      document.getElementById("map-display-question").textContent = `Show "${name}" to players?`;
      dialog.addEventListener("close", () => {
        resolve(["restore", "reset"].includes(dialog.returnValue) ? dialog.returnValue : null);
      }, {once: true});
      dialog.showModal();
    });
  };
  document.querySelectorAll("form[data-map-display]").forEach(form => {
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const action = await window.LGChooseFog(form.dataset.mapName);
      if (!action) return;
      form.elements.fog_action.value = action;
      HTMLFormElement.prototype.submit.call(form);
    });
  });
})();
