# Testing/deployment/architecture lossless split: manifests and indexes (2026-10-31)

Original source baseline: features/perplexity
e59a02f2bc6ff50cf059be40df60350cd06d2160.
The complete uploaded guides match the original live Git blobs:

- docs/testing.md: 23f3cfc1966c0923c9a0ad43bbb345079d074bee, 63257 bytes.
- docs/deployment.md: 73efb8bc94d19f6bb0442140893dfe394fdf9d9a, 47889 bytes.
- docs/architecture.md: 7d1b6a6cce9edc90be272305a522bb49d21b9415, 65461 bytes.

## Content delivery: all 122 sections verified

Testing 001-023: b14c34bbc2d018ca7f867adf44f30acc4b969089;
024-042: d7ed53c5627b92c23fce9b6b43dd40c1310dc22f.
All 42 committed source blobs match their slices. Exact reconstruction: 63257
bytes, SHA-256 15710ae2def97bfbaa1d71094fffc28a8413040b4d13045dfc99fb71f4930648.

Deployment 001-012: 77cb5bbbc052d76e738c99e10db4e5f4eef8180d;
013-036: c14088ffb53f226697b0e04cf76edf069f842640.
All 36 committed source blobs match their slices. Exact reconstruction: 47889
bytes, SHA-256 ecad8b97c0545edf12383e94e3a60540ec738f680ee237cd36312562075a4e07.

Architecture 001-022: 08c6b98216520ec04a04fc3a08b95351021eb710;
023-044: cbceac1b119ffa0cc7f68c9d9754247a90e26dc1.
All 44 committed source blobs match their slices. Exact reconstruction: 65461
bytes, SHA-256 87f917d4cd37b558edda20fab4c86f17513047e6c0ab5b3cd2399053676eb0e9.
Largest section sizes respectively: 5894, 4864 and 6328 bytes.

## Manifest and index finalization

This commit adds docs/testing/manifest.json, docs/deployment/manifest.json and
docs/architecture/manifest.json, and replaces the corresponding three root guide
paths with indexes. No source section is edited. Each compact format-1 manifest
records original commit/blob/bytes/SHA-256 and ordered path/bytes/SHA-256 entries.
Concatenate file bytes in files order; indexes/manifests are excluded.
Manifest sizes: 6947, 6037 and 7458 bytes. Index sizes: 6123, 4992 and 5810 bytes.
Prepared manifest Git blobs, in testing/deployment/architecture order:
d6c4b586d9b34b9f1ed4f0f7753e297341107c3a,
6a6ceba5283cea316042b641d47484ad534af2b4,
3f581d57b79d3c10f8edb79c6a5777416559e501.
Prepared index blobs in the same order:
032988353ec1cd2890c14c3c12bb4c4ed5841a2b,
8cab2b7597c9dd1681be5502514c367ec274aa56,
2426bc1c3935e3509329298c3dfb8bbbdef1d42c.
Check these against committed blobs after the successful write; preparation is
not a claim that the final write has already succeeded.

## Decisions, validation and limitations

Fence-aware extraction ignores heading-like text inside code fences. Full-source
reconstruction, per-file bytes/hashes, generated index content targets and file
size bounds were checked. Original section wording and relative links/fragments
stay verbatim. Resolve links against the former docs/<guide>.md base until
rebased. Other legacy fragments need review. Identified testing backup, viewer
synchronization and Fontconfig anchors, plus deployment campaign-backup anchor,
remain navigable in the root indexes through explicit onward links.

Historical commands, dependency names, two-check CI descriptions and room-note
statements may be obsolete. Indexes point at current ci-tests.md, recovery/backup
contracts and Bug 2 closure record 066 rather than silently rewriting source.
Bug 2 acceptance is unchanged. Existing historical handover/TODO/API/usage
manifests and evidence are untouched; these manifests identify split-time
snapshots, not future semantic edits. Git history preserves the source baseline.

README.md and HANDOVER.md were reviewed on the current branch. Existing README
guide links remain correct at the same paths, so README.md is unchanged. The
short HANDOVER.md pointer to this record remains a separate follow-up; it is
not part of this six-file manifest/index finalization and focused-record update.
No application tests, new CI result or deployment validation were executed or
claimed. Every delivery commit includes [skip ci]. No runtime files, dependencies,
migrations or archive-only Patch/ material change. Report actual delivery only
after the GitHub write succeeds.
