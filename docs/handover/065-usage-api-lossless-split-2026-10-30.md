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

## Partial usage stage: content 001-016 only

This stage adds docs/usage/001-016 as byte-preserved source slices (18813 bytes).
It does not replace docs/usage.md or add the usage manifest/index. The original
80085-byte usage monolith remains authoritative until the full set is delivered.
After the successful write, verify every returned section blob against the source.
Do not describe the complete two-guide split patch as finished.

Remaining: 26 usage content files (including an oversized section's continuation),
the usage manifest/replacement index, final combined split record and HANDOVER.md
index link. All content must be present before the usage root becomes its index.
The full prepared 42-file usage transformation reconstructs its source exactly,
with no file above 10000 bytes and fence-aware heading detection. Prepared-file
checks are not claims that all those files have been committed.

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
