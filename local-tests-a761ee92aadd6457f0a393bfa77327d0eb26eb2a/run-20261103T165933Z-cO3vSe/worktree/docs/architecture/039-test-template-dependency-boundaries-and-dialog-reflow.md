## Test template/dependency boundaries and dialog reflow

Browser test overrides now use a DictLoader followed by real web_html/templates
filesystem loaders, maintaining explicit layout overrides without copying every
shared partial. The helper's auxiliary GET responses do not intercept unknown
endpoints or writes. Full editor markup supplies the current script dependency
graph in gesture tests; viewer helpers precede viewer_display.js.

Floating native modal dialogs retain their normal top-layer/keyboard behavior.
A ResizeObserver coalesces content-size notifications through requestAnimationFrame
and clamps their existing position to the window bounds. Closing cancels a queued
frame. This does not recenter the dialog on every edit or modify draft/save scopes.


