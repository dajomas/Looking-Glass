## Installing cross-map passages (schema migration 12)

This incremental patch targets commit cbaf4890d5aba22dd50b42445b1c7109ef5fb8ee.
Stop both portals before installing. Back up the entire data directory, SQLite
file and any present WAL/SHM sidecars while stopped, along with your working tree.
Extract the archive at the repository root, preserving relative paths and replacing
only its listed files. Do not apply over an unrelated source snapshot or a schema
with a different migration 12. Review the changed files against the target source
version before replacing local modifications.

Restart through your normal launcher. The existing migration runner applies schema
12 automatically. Hard-refresh admin and viewer tabs. There are no new packages,
ports or config keys; the viewer default remains 5100. Marker/label settings default
on but no existing maps acquire endpoints automatically. Migration preserves the
prior map, arrow and fog data. Server-side marker labels try Windows Arial or Linux
DejaVu Sans and fall back to Pillow's built-in font; unsupported glyphs in the fallback
may not render. No fonts or other assets are downloaded.

Test on a copy of a campaign before live play, including one-way/return connections,
a secret endpoint, preserve/reveal arrival, stale-tab rejection and a deleted target.
Run HTTP/CSRF and real-browser tests in the installed project environment before
live use. See [testing](testing.md) for commands, prerequisites and manual checks;
a test command documented here is not a claim that it passed on every platform.

For rollback, stop both portals and restore the matching pre-patch code and complete
pre-upgrade data/database backup together. There is no down-migration. Do not lower
schema_version manually. Preserve the post-upgrade backup too if you may need to
recover newly authored endpoint links; wall exports do not carry these links.


