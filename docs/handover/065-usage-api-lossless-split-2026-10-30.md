# Usage/API lossless split: staged delivery (2026-10-30)

Baseline: features/perplexity 74115a4e7e82bf419ba141c448aff3900213bfc9.
The uploaded full guides match live Git blobs: docs/api.md is
265bef0b700271287d7b3fc44b5cf91411e9fb12 (49231 bytes); docs/usage.md is
11293cc01bed92b3521d3b8f018135370c07b007 (80085 bytes).

## Partial stage: API content 001-033; indexes not switched

API sections 001-016 were delivered in dd166c53a89bc3757ba9bd4ddd08f356d8555e67
and their committed blob hashes were verified against the original source.
This follow-up adds sections 017-033 byte-for-byte. After the successful write,
verify their returned blob hashes and the complete 33-file reconstruction.
No API manifest or replacement index is included in this content-only stage.
Do not describe the full split patch as complete.

Both docs/api.md and docs/usage.md remain unchanged monolithic guides and are
still the navigational authority. Remaining: the API manifest/index; all 42
usage content files and its manifest/index; final split record and HANDOVER.md
index link. Deliver all content before switching a guide's root to its index.

The complete prepared transformation was checked locally: 75 content files,
each at most 10000 bytes, reconstruct both sources byte-for-byte with ordered
SHA-256 manifests. Fence-aware headings avoid splitting inside examples.
Those complete-transformation checks are not evidence that all prepared files
have already been committed. Verify the actual returned commit and blob hashes
after each successful write. No application tests were executed.

README.md and HANDOVER.md were reviewed on the original baseline and remain
unchanged by these content-only stages; this focused record documents partial
delivery without cosmetic index changes. Historical manifests/evidence and
application code are untouched. Original relative links and wording remain
verbatim, with the same rebasing/anchor-review limitation as the earlier
HANDOVER/TODO splits. Semantic corrections follow extraction.

The user's explicit Bug 2 acceptance at 22:37 CET remains valid. This split does
not claim the manual upgrade exercise was executed, reopen acceptance, or finish
the separate accepted-status documentation updates. All split delivery commits
use [skip ci]; no new CI run or successful push is claimed until it occurs.
