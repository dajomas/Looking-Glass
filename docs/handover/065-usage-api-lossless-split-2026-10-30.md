# Usage/API lossless split: staged delivery (2026-10-30)

Baseline: features/perplexity 74115a4e7e82bf419ba141c448aff3900213bfc9.
The uploaded full guides match live Git blobs: docs/api.md is
265bef0b700271287d7b3fc44b5cf91411e9fb12 (49231 bytes); docs/usage.md is
11293cc01bed92b3521d3b8f018135370c07b007 (80085 bytes).

## API extraction and index

API content 001-016 was delivered in dd166c53a89bc3757ba9bd4ddd08f356d8555e67;
017-033 followed in 1db831f18ccea5d638c56401448d1db73119e966. All 33 committed
Git blob hashes were verified against the uploaded/live source slices. Their
ordered concatenation reconstructs the exact 49231-byte original source,
SHA-256 4c9b8055d0ad91107faeea4ec233e6bae05c28fba8b761d896dbe074d24cd849.
The largest API section is 6607 bytes; every section is below 10000 bytes.

This stage adds docs/api/manifest.json and replaces docs/api.md with a short
33-entry index. The manifest records original path, source commit/blob, original
size/hash and ordered section paths, titles, part numbers, byte counts and SHA-256
hashes. It describes the original snapshot, not later semantic edits. The index
is not part of source reconstruction. All index section links were checked
against the generated paths and the existing 33-file inventory. Index/manifest
JSON and source reconstruction were checked locally; verify the actual committed
index and manifest hashes after the write succeeds. These are documentation
checks, not application tests or a new CI result.

The API index flags that original relative links/fragments remain verbatim and
may resolve differently after relocation. Resolve them relative to the old
docs/api.md base until rebased. Old docs/api.md#... links also need review.
The original introductory error-envelope and room-note descriptions may predate
Bug 2; the index links the current room-note recovery contract rather than
silently rewriting preserved source bytes. Semantic corrections follow extraction.

## Remaining split work

The usage guide remains an unchanged monolith. All 42 usage content files,
its manifest and index, the final combined split record and HANDOVER.md index
link remain to be delivered. The API extraction/index stage does not complete
the whole prepared two-guide split patch or the accepted-status Bug 2 edits.

README.md and HANDOVER.md were reviewed on the original baseline and remain
unchanged in the content/index stages; this focused record preserves delivery
and verification history without cosmetic index changes. Existing historical
manifests/evidence and application code are untouched.

The user's explicit Bug 2 acceptance at 22:37 CET remains valid. This split does
not claim the manual upgrade exercise was executed, reopen acceptance, or finish
the separate accepted-status documentation updates. All split delivery commits
use [skip ci]; no new CI run or successful push is claimed until it occurs.
