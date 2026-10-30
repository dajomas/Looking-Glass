# Usage/API lossless split: staged delivery (2026-10-30)

Baseline: features/perplexity 74115a4e7e82bf419ba141c448aff3900213bfc9.
The uploaded full guides match live Git blobs: docs/api.md is
265bef0b700271287d7b3fc44b5cf91411e9fb12 (49231 bytes); docs/usage.md is
11293cc01bed92b3521d3b8f018135370c07b007 (80085 bytes).

## API extraction and index: delivered

API content 001-016 was delivered in dd166c53a89bc3757ba9bd4ddd08f356d8555e67;
017-033 followed in 1db831f18ccea5d638c56401448d1db73119e966. All 33 committed
Git blob hashes were verified against uploaded/live source slices. Their ordered
concatenation reconstructs the exact 49231-byte original source, SHA-256
4c9b8055d0ad91107faeea4ec233e6bae05c28fba8b761d896dbe074d24cd849.
The largest API section is 6607 bytes; every section is below 10000 bytes.

API manifest and replacement index were delivered in
d8ec1b82169049745759b593622a86f2ad911dbe. Their committed Git blob hashes match
the generated files: manifest 4a43c617546b6d3eb1688f6026ef04cb489d468d;
index c445749ffab63637ad74118cc61d7f58219e88c2. The manifest describes the
original snapshot, not later semantic edits; the index is not part of source
reconstruction. Its 33 section links were checked against the inventory.

The API index flags that original relative links/fragments remain verbatim and
may resolve differently after relocation. Resolve them relative to the old
docs/api.md base until rebased. Old docs/api.md#... links also need review.
Original introductory error-envelope and room-note descriptions may predate
Bug 2; the index links the current recovery contract rather than silently
rewriting preserved source bytes. Semantic corrections follow extraction.

## Usage content: complete set staged; index not switched

Usage content 001-016 was delivered in 799fd5d46045b374af387204a39dec79ba51017b;
all 16 committed blobs matched their source slices, totaling 18813 bytes.
This follow-up stages the remaining 26 content files (61272 bytes). Source
section numbers end at 041, with section 020 split into part-01 and part-02;
there are 42 content files in total. Do not invent or renumber a section 042.

The full generated set reconstructs the original 80085-byte usage guide exactly,
SHA-256 ca61942f723010f0b90641bbbb7fdeccd020d3382cc40e7e0aa20ea023d8b150.
Its largest content file is 9816 bytes. Fence-aware heading detection preserves
example room headings inside code blocks rather than splitting them as sections.
After a successful write, verify all returned content blobs and reconstruction.
Prepared reconstruction checks do not substitute for that committed-file check.

The usage root docs/usage.md remains unchanged and authoritative at this stage.
No usage manifest or replacement index is included. Remaining structural work:
usage manifest/index, final combined split record and HANDOVER.md index link.
The two-guide patch is not fully applied until those pieces are delivered.

README.md and HANDOVER.md were reviewed on the original baseline and remain
unchanged in the staged content/index commits. This focused record captures
scope and validation without cosmetic index changes. Historical manifests and
evidence are untouched. Original usage wording/relative links remain verbatim,
with the same relocation caveat as API and the earlier HANDOVER/TODO splits.

The user's explicit Bug 2 acceptance at 22:37 CET remains valid. No manual upgrade
exercise, new application test execution or new CI result is claimed by these
structural changes. Accepted-status documentation finalization remains separate.
All split delivery commits use [skip ci]; report actual commits only after writes
succeed. No archive-only Patch/ material is committed.
