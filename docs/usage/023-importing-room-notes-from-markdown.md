## Importing room notes from Markdown

Open Import room notes in the right-hand Room notes panel, choose a UTF-8 `.md`,
`.markdown` or `.txt` file, and click Import notes. The importer uses the highest
heading level actually present (the lowest number: H1 before H2). Each heading
at that level becomes a room name. Everything after it, up to the next heading
at the same level, becomes that room's Markdown note. The room-name heading
itself is excluded; lower headings remain in the note. ATX (`#`) and Setext
(underlined) headings are supported. Headings inside code, quotes or lists do not
split rooms. Heading inline formatting is reduced to a plain name.

Example:

```markdown
## Entrance Hall
A cold breeze blows through the broken doors.

### Features
- Two cracked statues.

## Burial Chamber
Dust covers the stone coffins.
```

This creates Entrance Hall and Burial Chamber; Features stays in Entrance Hall's
note. See docs/examples/room-notes.md for another complete file. A single `# Dungeon`
document title above `## Room` headings creates ONE imported room named Dungeon;
omit that title if the H2 headings should be individual rooms. Preamble text before
the first room heading is ignored and reported. Reference-link definitions should
be included in each section that needs them; definitions elsewhere are not copied.

After importing, enable Select room (fog unchanged) and click any room.
Click Edit room. Use imported room notes is available inside the editor whether or not the room already has a name or note.
Choose a name from the dropdown; the name and note load together into an unsaved
edit draft. Review or adjust them, then Save room to assign them. Cancel discards
the selection. Selecting an imported entry replaces both fields in a draft, including for existing named rooms.

Imports are stored per map, persist across restarts, and do not affect fog or
existing rooms. Assigned names are hidden from subsequent dropdown choices until released. Reimporting identical
name/content pairs does not duplicate them. Changed content appends a new entry
rather than replacing a previous entry or assigned room. Same-name variants have
an ID suffix in the dropdown. Unassigned imported records can be removed using List imported notes (see below).
Reload the editor to see imports made by another admin session.

Limits: 1 MiB per UTF-8 file, 500 room sections per import, 200 characters per
room name, and 100,000 characters per note. Empty sections are allowed. Invalid
files are rejected as a whole, without partially adding entries. Imported content
is sanitized by the existing renderer after assignment, like manually entered notes.

### Clearing and replacing room metadata

Import room notes is a collapsible section, closed by default on each page load.
Click its summary to expand it. It remains collapsible independently of the whole
right panel. An explicit closed-details CSS rule keeps its form hidden even with
generic form layout styles. Expanding it is not persisted between page loads.

To remove metadata, click Edit room and Clear name and notes, then Save room.
Clear changes the draft only; Cancel restores the previous saved content. You
can also erase either field individually: names are optional, so notes-only rooms
are supported. Both blank fields clear the room's displayed metadata, without
changing fog, walls, imported entries or other rooms. Blank names display the
placeholder “Unnamed room”. This clears the stored text, not an encrypted/secure
wipe of historical database backups.

The imported-note dropdown is offered for every selected room inside Edit room only.
Choose a replacement to fill the current edit draft with the imported name and note.
Save room applies it; Cancel restores the previous values. Replacement is still
subject to revision and geometry checks. While editing, choose another imported entry directly from the dropdown; a different
unsaved draft prompts before being replaced.

