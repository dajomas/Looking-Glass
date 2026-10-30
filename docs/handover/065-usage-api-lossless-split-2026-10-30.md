# Usage/API lossless split: final manifest and index (2026-10-30)

Original source baseline: features/perplexity
74115a4e7e82bf419ba141c448aff3900213bfc9.
API source: Git blob 265bef0b700271287d7b3fc44b5cf91411e9fb12, 49231 bytes.
Usage source: Git blob 11293cc01bed92b3521d3b8f018135370c07b007, 80085 bytes.

## API extraction and index: delivered

API content 001-016 was delivered in dd166c53a89bc3757ba9bd4ddd08f356d8555e67;
017-033 followed in 1db831f18ccea5d638c56401448d1db73119e966. All 33 committed
Git blob hashes were verified against the original source slices. Their ordered
concatenation reconstructs the exact original, SHA-256
4c9b8055d0ad91107faeea4ec233e6bae05c28fba8b761d896dbe074d24cd849.
The largest API section is 6607 bytes. API manifest and replacement index were
delivered in d8ec1b82169049745759b593622a86f2ad911dbe; their verified Git blobs
are 4a43c617546b6d3eb1688f6026ef04cb489d468d and
c445749ffab63637ad74118cc61d7f58219e88c2 respectively.

## Usage finalization

Usage content 001-016 was delivered in 799fd5d46045b374af387204a39dec79ba51017b;
the remaining 26 files followed in a30c9815d3592998f13c8bbc4cb2f9886e079cf3.
Post-write verification found 40 exact source blobs and one extra trailing newline
in each of 020-cross-map-passages-migration-12-part-02.md and
021-collapsible-map-editor-help.md. This finalization removes only those two extra
bytes, adds docs/usage/manifest.json and replaces docs/usage.md with its index.
No section wording is otherwise changed.

The 42 source files use section numbers 001-041, with section 020 in two parts.
The generated full reconstruction is exactly 80085 bytes, SHA-256
ca61942f723010f0b90641bbbb7fdeccd020d3382cc40e7e0aa20ea023d8b150.
The largest content file is 9816 bytes. The compact manifest is 9400 bytes and
uses the same format as the API manifest. It describes the original snapshot,
not later semantic edits. The replacement index is excluded from reconstruction.

Validation before the final write: source blob identity, 42-file reconstruction,
per-file byte counts/SHA-256 hashes, index content targets and the five README
usage-topic anchors were checked. The two corrected source blobs must be
7d6287fdfc28623c526bedf3ca9b94c01b40d76c and
4610ab308b00da686f06cf78f2844b243d0732f1. Verify committed blobs after the write;
prepared-file checks do not claim that the final write has already succeeded.

## Limitations and unfinished work

Original relative links and fragments inside section files remain verbatim.
Relocation can change their meaning; resolve them relative to the former
docs/api.md or docs/usage.md base until deliberately rebased. Other old fragment
links still need review. The usage index retains five README-linked topic
anchors and points at the current room-note recovery/backup contracts because
original room-note wording may predate Bug 2. Semantic corrections are separate.

README.md and HANDOVER.md were reviewed at the unchanged live baseline. README.md
needs no modification for this index. The short HANDOVER.md index link and broader
accepted-status documentation finalization remain separate follow-up work; this
commit updates the existing focused split record instead of adding detailed history
to the root index. Existing historical manifests and evidence remain untouched.

The user's Bug 2 acceptance at 22:37 CET remains valid. No new application tests,
manual upgrade exercise or new CI success are claimed. All split commits use
[skip ci]. No runtime code, dependency, migration or archive-only Patch/ material
is changed. Report the actual final commit only after the GitHub write succeeds.
