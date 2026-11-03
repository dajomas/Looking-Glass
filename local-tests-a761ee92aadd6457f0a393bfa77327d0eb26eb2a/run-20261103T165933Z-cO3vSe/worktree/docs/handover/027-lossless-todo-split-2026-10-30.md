# Lossless TODO split (2026-10-30)

Documentation-only preparation against features/perplexity at
4d92460564ef0276b8ebb6bb08d43bb037752294. TODO.md becomes an index linking
17 verbatim sections under docs/todo/: workflow/scope, 15 bugs and validation
caveats. No TODO.sh is introduced. No application code, schema, workflow,
bug status or acceptance requirement is changed. Bug 2 remains open.

Preparation verified the complete original against Git blob
16471b8f71a4623fb21b279867de7a5df8d3c7fa, exact 29,464-byte concatenation,
per-section sizes/SHA-256 hashes, sequential bug headings 1-15, unchanged
11 checked/4 unchecked statuses and all 18 new TODO-index links. The largest
content file is 3,232 bytes. No application, HTTP, browser, workflow or deployment
tests ran; historical validation claims are not new results.

README.md was reviewed and needs no change for this split. HANDOVER.md only
adds this entry. Historical handover sections 001-026 and their reconstruction
manifest remain untouched. docs/todo/manifest.json records the original source
and reconstruction order; future section edits invalidate its split-time hashes,
with the original snapshot retained in Git history. Root-relative prose and
historical phrases retain their original context; external old TODO fragment
links require updating. No files are deleted/renamed or deployment steps needed.
