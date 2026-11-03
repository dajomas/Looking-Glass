## Fog editor import notifications

After a map import redirects to the fog editor, the import result appears at the
bottom center of the map section, not over the Search or Checkpoint buttons.
Server-rendered success and error messages share this location in the editor.
Long messages wrap within the viewport width. The message overlay does not
intercept map clicks. Other pages keep their existing message placement.
This change does not alter upload progress, import processing, or the existing
JavaScript toast lifecycle.

