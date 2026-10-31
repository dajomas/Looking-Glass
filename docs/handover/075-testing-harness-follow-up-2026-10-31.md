# Testing harness follow-up: diagnostic packaging (2026-10-31)

Preparation baseline: dajomas/Looking-Glass, features/perplexity,
95275c0b68cd9cdb069b302e38ade6278cf534ad, verified as live tip.
Bug 15 remains accepted and closed by record 074. This is a separate harness
follow-up, not a reopening or a new Bug 15 execution/acceptance claim.

## Packaging implementation and compatibility

runtests.sh previously passed test-results/* directly to gzip. Directories
produced ignored-directory diagnostics and a nonzero pipeline exit even when
regular logs were compressed. Its baseline blob was
b919da2aecb003626c237169d15659dd65dddce2; only the packaging tail changes.

New tools/package_test_results.py creates two sibling outputs for a prefix:
- PREFIX.txt: concatenated gzip members encoded as base64, retaining the legacy
  decoded non-hidden top-level regular-file contents in bytewise name order.
  This is a flat-log product, not the complete nested diagnostic tree.
- PREFIX.diagnostics.tar.gz: the complete results tree, rooted at test-results/,
  preserving relative paths, nested/hidden files, binary evidence and empty dirs.

The runner uses prefix test-results.SHORTSHA, with unversioned fallback as before.
Existing base64/gzip decoding remains valid for the .txt; full diagnostics must
use the additional bundle. No consumer is silently switched to tar. The GitHub
collector getworkflow.sh and CI artifact workflow are unchanged.

Outputs must be outside the source tree. Symlinks, dangling links and special
files are refused rather than followed or silently omitted. Both products are
prepared before publication; temporary files are cleaned after ordinary failure.
Each final replacement is atomic, but the pair is not a transaction or a
crash/power-loss guarantee. On failure, do not mistake prior output files for
fresh evidence. Review logs/bundles for sensitive data before sharing.

Test-stage failures remain failures after successful packaging. Packaging failure
also returns a failed runner status. Browser/live selection and existing failure
assertions are unchanged; no skipped/excluded tests manufacture success.

## Executed preparation evidence

Python 3.12.8 isolated sandbox, exact new helper/tests and real Bash runner with
controlled stand-ins for application pytest, Node and browser preflight commands:
- Original runner plus the new helper/regressions staged: 6 failed, 10 passed
  in 0.30s. This isolates the packaging-tail baseline, not an untouched full checkout.
- Candidate: 16 passed in 0.49s; JUnit and captured output generated.
- Candidate Bash syntax check passed; new Python source compiled.

Tests round-trip nested binary data, spaces, hidden evidence and empty dirs;
compare legacy decoded bytes against gzip/base64; refuse symlinks/FIFOs and
inside-source outputs; preserve previous products on preparation failure; and
exercise each runner stage's failure status plus packaging failure. These are
harness regressions, not real application/browser/live/container execution.
Full checkout and exact-source CI validation remain pending.

## Use and remaining follow-up

Run the existing runner from the normal configured test environment. It now
prints both output paths. For the focused harness checks:

```bash
python -m pytest -q python/tests/test_test_results_packaging.py
```

Podman support is the next scoped change and is NOT delivered here. The existing
container module still requires Docker; the two reported setup errors have not
been rerun or reclassified as passed. Planned engine selection must support
Podman directly, keep explicit selection failures visible, preserve Docker CI
coverage and account for rootless/SELinux test mounts without weakening checks.
No real Podman/Docker execution or new CI result is claimed.

README.md was reviewed and matches live blob
d118df868f67d479001edb5111c279f988d2e642. Its runner overview remains accurate;
no cosmetic edit is needed for this packaging-only step. HANDOVER receives one
short pointer. Preserve records 074 and earlier, historical split manifests,
application runtime, requirements, workflows and other branches. No delivery
archive or Patch/ material is added to the repository.
