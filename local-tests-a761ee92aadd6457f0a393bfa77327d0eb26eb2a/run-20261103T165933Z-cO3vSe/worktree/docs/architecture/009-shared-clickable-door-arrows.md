## Shared clickable door arrows

`services/door_arrows.py` shares midpoint/normal sampling, polygons, raster
rendering and server hit validation. Ordinary doors require distinct adjacent
labels with one revealed side. Secret-origin doors keep arrows after both sides
are revealed. Portal Entries resolve to the configured side of the paired element,
using verified open pixels, never a client-provided destination. Exit hints are
noninteractive, admin-only and may be drawn outside revealed areas.

The `MapSpec.arrow_audience` discriminator separates admin and viewer cache
identity. Viewer composition excludes undiscovered secrets and Exit-only hints;
locked/unlocked hints use ordinary appearance. The viewer API still contains no
wall graph, hidden routing coordinates or mutation endpoint.

