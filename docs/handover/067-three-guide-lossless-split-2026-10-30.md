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
newline state. Each guide also has a compact reconstruction manifest and
replacement index. No source wording or historical commands/results are
semantically corrected. Prepared-file checks are not committed-file verification.

## Testing content: delivered and verified

Sections 001-023 were delivered in b14c34bbc2d018ca7f867adf44f30acc4b969089;
024-042 followed in d7ed53c5627b92c23fce9b6b43dd40c1310dc22f. All 42 committed
Git blobs matched their source slices. Ordered concatenation reconstructs the
exact original 63257 bytes, SHA-256
15710ae2def97bfbaa1d71094fffc28a8413040b4d13045dfc99fb71f4930648.
The testing manifest and replacement index are not yet delivered.

## Deployment content: delivered and verified

Sections 001-012 were delivered in 77cb5bbbc052d76e738c99e10db4e5f4eef8180d;
013-036 followed in c14088ffb53f226697b0e04cf76edf069f842640. All 36 committed
Git blobs matched their source slices. Ordered concatenation reconstructs the
exact original 47889 bytes, SHA-256
ecad8b97c0545edf12383e94e3a60540ec738f680ee237cd36312562075a4e07.
The largest section is 4864 bytes. Deployment manifest/index remain pending.

## Architecture content stages

Sections 001-022 were delivered in 08c6b98216520ec04a04fc3a08b95351021eb710.
All 22 committed blobs match their source slices (34680 bytes), rechecked
before preparing this follow-up. This stage adds sections 023-044 (30781 bytes),
not the manifest/index. The full generated 44-file set reconstructs 65461 bytes
exactly, SHA-256
87f917d4cd37b558edda20fab4c86f17513047e6c0ab5b3cd2399053676eb0e9.
Compare all 44 committed section hashes against source slices after a successful
write. Historical descriptions, including room-note wording predating Bug 2,
remain verbatim; this is not a semantic correction or a reversal of acceptance.

All three monolithic guide paths remain unchanged and authoritative. Remaining:
three manifests and three replacement indexes, final verification and a short
HANDOVER.md link. Do not describe the complete three-guide split as delivered
until all are present.

## Decisions and limitations

README.md and HANDOVER.md were reviewed at the unchanged live baseline. Their
existing guide links remain correct; no cosmetic edits are made in this content
stage. This focused record tracks progress; the root handover pointer follows
during finalization. Existing handover/TODO/API/usage manifests and evidence
remain untouched. Original relative links and fragments remain verbatim; resolve
them against each old docs/<guide>.md base until deliberately rebased. Legacy
fragment links require review at index switch. No new application tests, CI
success or deployment validation is claimed. Every delivery commit includes
[skip ci]. No runtime files, dependencies, migrations or archive-only Patch/
material are changed.
