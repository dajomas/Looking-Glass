## Automatic editor entry for unnamed rooms

After room-at lookup passes existing selection generation/dirty checks, select()
shows the saved room, then enters editing only when the selection is explicit,
the selection-mode checkbox is currently checked, and the returned room name is
blank after trimming. Notes content is not part of this condition. No saved data
is altered, no dirty flag is set, and no additional HTTP request is made. Name
focus is only applied if the panel body is expanded. The generic show() function
is unchanged so Save, Cancel and background updates cannot accidentally auto-edit.

