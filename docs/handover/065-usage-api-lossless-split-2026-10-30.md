# Usage/API lossless split: staged delivery (2026-10-30)

Baseline: features/perplexity 74115a4e7e82bf419ba141c448aff3900213bfc9.
The uploaded full guides match live Git blobs: docs/api.md is
265bef0b700271287d7b3fc44b5cf91411e9fb12 (49231 bytes); docs/usage.md is
11293cc01bed92b3521d3b8f018135370c07b007 (80085 bytes).

## Partial stage: API content 001-016 only

This commit adds the first 16 content files under docs/api/, copied byte-for-byte
from the source guide. It does not replace docs/api.md or docs/usage.md. The
original monolithic guides remain the navigational authority until their full
content sets, indexes and manifests are delivered. Do not describe this stage
as completion of either guide split or the complete prepared patch.

Remaining: API files 017-033 and its manifest/index; all 42 usage content files
and its manifest/index; final split record and HANDOVER.md index link. Deliver
remaining content before switching a guide's root file to its new index.

The complete prepared transformation was checked locally: 75 content files,
each at most 10000 bytes, reconstruct both sources byte-for-byte with ordered
SHA-256 manifests. Fence-aware headings avoid splitting inside examples.
Those complete-transformation checks are not evidence that all files have
already been committed. Verify the stage's actual returned commit and blob
hashes after each successful write. No application tests were executed.

README.md and HANDOVER.md were reviewed on the unchanged baseline; this focused
record documents the staged delivery without cosmetic index changes. Historical
manifests/evidence and application code are untouched. Original relative links
and wording remain verbatim, with the same rebasing/anchor-review limitation
as the earlier HANDOVER/TODO splits. Semantic corrections follow extraction.

The user's explicit Bug 2 acceptance at 22:37 CET remains valid. This split does
not claim the manual upgrade exercise was executed, reopen acceptance, or finish
the separate accepted-status documentation updates. All split delivery commits
use [skip ci]; no new CI run or successful push is claimed until it occurs.
