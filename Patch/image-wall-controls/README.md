# Pack images, wall-type controls and portable launchers

## Base and scope

Apply to `b04a92468ad47d0a2c618b18035a7d345c402704` on `features/development`.
The user-supplied base64 source archive is the byte-level comparison baseline.
This patch builds on the reusable campaign-scoped wall-source feature already
present in that archive. It does not replay the earlier wall-source patch.
Viewer default 5100 is preserved.

## Apply

Stop the server and back up the application SQLite database (including WAL
state via a proper SQLite backup) and data/maps. Commit or stash local work.
Extract the changed-files ZIP into the repository root, preserving paths;
it contains full replacement files, not the complete application.
Alternatively apply Patch/changes.patch with git apply --check and git apply
instead of overlaying the replacement files. Do not do both.

```bash
git switch features/development
git rev-parse HEAD  # confirm the base above
git status --short
# Extract this archive in the repository root, then:
chmod +x run.sh
./run.sh
```

Migration 3 is applied on normal startup. Existing maps keep all categories
initially enabled and retain their current artwork. New artwork imports are
normalized to a single oriented PNG; there is no separate viewer-art setting.
Rollback: stop the tool, restore the pre-patch code and matching database/maps
backup. Do not remove applied migration entries from a live database.

## Changes and important behavior


## Pack artwork and consistent screens

In Saved wall sources, save a `.db`, JSON, Universal VTT, or `.zip` pack,
select its wall set, and optionally tick **Use image from this wall set on BOTH
screens** before applying. Unticked (the default) retains your current artwork.
Selection is reset when changing wall sets, preventing accidental reuse of a
previous image choice. Applying replaces this map's walls; it does not alter
other maps using the saved source.

Supported artwork is a Foundry `background.src` or legacy `img` data URI,
a Universal VTT base64 `image`, or a referenced file included in a ZIP alongside
scene exports. ZIP references are matched by their full pack-root path or a
path relative to the scene file. Paths are case-sensitive. Nested archives,
absolute/traversal paths and duplicate normalized archive paths are rejected.
ZIPs are limited to 2,000 entries and 150 MiB total expanded content; individual
uploads and decoded images also obey `storage.max_upload_mb`. Unsupported
metadata JSON is skipped. Supported images are validated using the normal
image-import path and pixel limits.

Foundry exports commonly contain only an external path and a small embedded
`thumb`. When only that thumbnail is embedded, it is explicitly labelled as low
resolution and never selected automatically. Upload the full-resolution art or
include it in a ZIP for best results. URLs and local Foundry module paths are
not fetched or read from the server filesystem. Existing databases are reusable
without being uploaded again, because image metadata is parsed from saved bytes.

There is one canonical `maps.image_file` per map, not separate DM/player images.
Every newly imported image is normalized to an oriented, static RGB PNG (first
frame for animated inputs). Both admin artwork and viewer fog compositing use
that file. The viewer may downscale/re-encode it and adds fog; it never receives
an alternate scene image, the raw image endpoint, or wall data. Replacing artwork
updates image dimensions, wall/fog versions and cache keys; admin refreshes its
versioned image URL and viewers receive the existing refresh notification.
The currently selected active map must be the map being compared: another map
can still be edited while the viewer displays the campaign's active map.

Auto-align uses the selected image dimensions. Disable auto-align to preserve
manual offsets/scales. Applying artwork or changing boundaries retains fog
history and replays it against the new geometry; blank the viewer first and
reset fog if old reveals are inappropriate. Source deletion leaves copied map
artwork and walls intact.

## Wall legend and type controls

| Type | Overlay | Boundary behavior when enabled |
|---|---|---|
| Normal wall | Magenta solid | Blocks areas |
| Door | Blue solid | Blocks when Doors split areas is on |
| Secret door | Purple dashed | Blocks when Doors split areas is on |
| Window / terrain | Green solid | Blocks areas |
| Invisible wall | Yellow dashed | Blocks areas |
| Ethereal | Grey dashed | Never blocks (source semantics) |

Each legend row has **Show** (DM overlay only, page-local) and **Enabled**
(persistent per-map boundary participation). Press **Apply wall types** to save
the Enabled switches and recalculate fog on the server. Disabled categories
remain stored and visible at reduced opacity unless Show is unticked, so they
can be re-enabled without re-import. Ethereal can be toggled but remains
non-blocking even when enabled. The global Show walls checkbox still hides all
overlays. The existing Doors split areas toggle is an additional gate for both
door categories. Filters are independent of source selection and survive
re-import. Disabling boundaries can merge rooms and expand prior reveals;
confirmation warns to blank the viewer before recalculating.

## Portable launchers

Use `./run.sh` (Bash), `run.bat` (Windows Command Prompt), or `./run.ps1`
(PowerShell). Bash users may first run `chmod +x run.sh`. Python 3.12+ must
already be installed (3.14 is recommended). `LG_PYTHON` can specify the full
path to an interpreter; it is an executable path, not a command with arguments.
All launchers change to the repository directory, create `.venv` if needed,
and install runtime requirements on first use or when requirements.txt changes.
First setup needs package-index access; later launches do not run pip unless needed.
Use `--install` to rerun pip, or `--no-install` to skip dependency setup for an
already provisioned venv. Setup failures stop startup and preserve the exit code.
No administrator privileges or global package installation are required.

Arguments are forwarded to the existing CLI, for example:

```bash
./run.sh --no-install -c config.yaml serve
./run.sh create-user dm --role admin
```

```powershell
./run.ps1 --no-install -c config.yaml serve
```

```bat
run.bat --no-install -c config.yaml serve
```

Defaults remain admin 5000 and viewer 5100. Config-file settings and
`LG_ADMIN_PORT` / `LG_VIEWER_PORT` overrides are respected; launchers do not
force ports. Ctrl+C stops the tool. PowerShell must permit local scripts under
your organization's execution policy; the launcher does not change that policy.

## Regression and limitations

See TEST_REPORT.md for executed and unexecuted checks, and sample-image-summary.json
for the supplied pack's actual artwork availability. This patch intentionally
does not download external artwork or treat Foundry module paths as server paths.
Full-resolution referenced artwork must be supplied by the DM or included in ZIP.
No image selection exists on the viewer portal; it always uses the map's selected
artwork beneath fog. "Same image" does not mean the DM loses the translucent fog
overlay or that players receive the unfogged source.

The platform wrappers use one Python bootstrap to avoid three diverging setup
implementations. They do not change PowerShell execution policy or install Python.
