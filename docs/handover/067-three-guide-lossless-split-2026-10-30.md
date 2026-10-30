# Testing/deployment/architecture lossless split: staged delivery (2026-10-30)

Baseline: features/perplexity e59a02f2bc6ff50cf059be40df60350cd06d2160.
The complete uploaded guides match their live Git blobs:

- docs/testing.md: 23f3cfc1966c0923c9a0ad43bbb345079d074bee, 63257 bytes.
- docs/deployment.md: 73efb8bc94d19f6bb0442140893dfe394fdf9d9a, 47889 bytes.
- docs/architecture.md: 7d1b6a6cce9edc90be272305a522bb49d21b9415, 65461 bytes.

## Generated transformation

Fence-aware extraction produces 42 testing, 36 deployment and 44 architecture
content files. Every generated content file is below 10000 bytes. Ordered
concatenation reconstructs each exact original, including line endings and final
newline state. These are prepared-file checks, not committed-file verification.
Each guide also has a compact reconstruction manifest and replacement index.
No source wording or historical commands/results are semantically corrected.

## First content stage

This stage adds testing content 001-023 only (18477 original source bytes).
The three monolithic guide paths remain unchanged and authoritative. No guide
manifest/index is switched in this stage. After a successful write, compare
returned Git blob hashes against the corresponding generated source slices.

Remaining: testing 024-042, all deployment/architecture content, three manifests
and three replacement indexes, final verification and a short HANDOVER.md link.
Do not describe the complete three-guide split as delivered until all are present.

## Decisions and limitations

README.md and HANDOVER.md were reviewed at the live baseline. Their existing
guide links remain correct; no cosmetic edits are made in this content stage.
This focused record tracks progress; the root handover pointer follows during
finalization. Existing handover/TODO/API/usage manifests and evidence remain
untouched. Bug 2 acceptance is unchanged. Original relative links/fragments are
preserved verbatim and must be resolved against each old docs/<guide>.md base
until deliberately rebased. Legacy fragment links require review at index switch.
No new application tests, CI success or deployment validation is claimed.
Every delivery commit includes [skip ci]. No runtime files, dependencies,
migrations or archive-only Patch/ material are changed.
