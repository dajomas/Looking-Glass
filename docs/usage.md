# Usage guide

## First run

Start Looking Glass, read the generated superadmin password from the log, sign
in on the admin portal, and change the password. Create DM/admin accounts and
viewer accounts as required. Campaign owners manage their own campaigns and
assign viewers from the campaign page. Portal ports follow your configuration.

## Preparing maps

Create a campaign, then use its single-map import for one image and optional
Foundry VTT / UVTT walls. A single-set wall source can be applied automatically;
a multi-set source is saved for explicit selection. For several images and
independent wall files, use **Import multiple maps and assign walls** on the
same page. See [the batch workflow](campaign-batch-import.md).

## Saved wall sources

In **Walls → Saved wall sources**, save a supported Foundry database/JSON,
UVTT, or supported pack. Choose the saved source, then a wall set. Lists use
case-insensitive alphabetical/numeric ordering and preserve original scene
indices. One database can supply different sets to different maps. Reusing a
saved source requires no re-upload within the same campaign. Duplicate uploaded
bytes use the existing server deduplication; a changed source becomes a new one.

**Apply selected wall set** takes effect immediately: there is no confirmation.
The same applies to campaign wall assignments and Apply alignment. If optional
pack-image controls are present, opting in replaces artwork immediately too.
Otherwise artwork is retained. Blank the viewer before changing boundaries:
existing reveal clicks are retained and recalculated against the new walls.

The duplicate one-off wall import form, its Import walls and Clear buttons,
and their JavaScript handlers have been removed. Import through Saved wall
sources instead. The old API endpoints remain available for existing clients.
Delete source still confirms; deleting a reusable source does not remove walls
or artwork already copied to maps. Sources remain private to their campaign.

## Wall legend and alignment

The map editor displays a six-type wall legend:

| Type | Colour/style | Meaning |
|---|---|---|
| Normal | Magenta solid | Separates areas |
| Door | Blue solid | Follows Doors split areas |
| Secret door | Purple dashed | Follows Doors split areas |
| Window/terrain | Green solid | Separates areas |
| Invisible | Yellow dashed | Blocks movement |
| Ethereal/passive | Grey dashed | Does not separate areas |

This is a visual colour/style key, not a new persistent wall-type filtering
control. Show walls affects only the DM overlay. Doors split areas affects
boundary calculation. Alignment maps source coordinates to the current image:
`image = (wall - offset) * scale`. Use offsets, scales and nudges, then Apply
alignment. Check the exact player preview after changing geometry.

## Showing and switching battle maps

Each campaign **Show**, editor **Show to players**, and editor map-switch
selection asks the server afresh whether the target has restorable reveals.
The response is not cached or reused across targets/selections.

- If no effective reveals remain, no dialog appears. The map is displayed
  with reset reveals, discarding any old operation/undo history.
- If effective saved reveals remain, the Restore / Reset / Cancel dialog
  appears. Restore replays the checkpoint; Reset starts fully fogged; Cancel
  leaves the current display unchanged.
- A history containing only hide operations, reveal-then-hide, or a final Reset
  does not count as restorable merely because operations exist.

The editor map-switch now activates the selected target before opening its
editor. A cancelled choice or failed availability check keeps the current
selection/display. Directly opening an editor URL is still an editing action,
not automatic activation. Blanking needs no restore dialog.

A failed availability request never silently resets or displays a map. An active
map is evaluated from its live operations; an inactive map is evaluated from its
saved last-displayed checkpoint. Without a checkpoint there is no restore offer,
including never-displayed maps with offline-prepared clicks: they start reset.
Saved clicks are evaluated against current walls, not historical geometry.

## At the table

Assign viewers, open the viewer portal, and show a map. Click a room in Reveal
mode to reveal its wall-bounded area; Hide mode hides it. Undo, Reveal all and
the separate toolbar Reset remain available. Toolbar Reset remains undoable;
display Reset discards the previous history. Pan with right/Space drag and zoom
with the wheel; F fits. Use Player preview or Open exact player image to inspect
what players see. Blank sends viewers to the waiting screen. Players receive a
server-composited fogged image, not the raw map or wall data.

## Updating

Deploy all files together, restart the server for the added display-options
endpoint, and hard-reload DM/campaign tabs. This patch adds no schema migration;
the previously deployed checkpoint/token schema must already be present. Read
[the interaction notes](interaction-refinement.md) for checks and limitations.
