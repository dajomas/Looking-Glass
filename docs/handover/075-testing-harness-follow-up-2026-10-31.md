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
use the additional bundle. The GitHub
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

## Podman adapter foundation: integration still pending

Packaging was delivered in 4027ef70fc6193e8f1a56581d0bf0f1c80d20171,
verified as the live tip before preparing this foundation. This section adds
test-only adapter contracts; it does NOT wire the two Recovery tests yet.
Their Docker-only setup assertion remains until a subsequent exact-approved
integration commit. Do not claim the two checks now run on Podman or passed.

New python/looking_glass_test_container.py resolves LG_CONTAINER_ENGINE as
auto, podman or docker. Auto prefers an installed Podman binary, then Docker
only if Podman is absent. Explicit selection never falls back. Preflight runs
version/info and records selection, executable and native command output. A
selected but unusable engine fails visibly. Commands are argument arrays with
stdin closed, not shell strings. Nonzero exits, execution errors and timeouts
are logged; check=False is reserved for callers' diagnostic/cleanup handling.

Native build-pull flags differ for Podman and Docker. Podman config mounts use
a private read-only :ro,Z relabel of the disposable file, not label=disable or
recursive host chown. Symlink config paths are refused. Published URLs require
one explicit 127.0.0.1 binding for each listener, valid distinct host ports and
complete inspect data; malformed/nonloopback bindings are not tolerated.

Preparation: new helper/tests compiled under Python 3.12.8; isolated pytest
reported 35 passed in 0.32s, no skips. Tests execute fake native binaries for
Podman-only/Docker-only/both-engine selection, preflight, command logging, no
shell interpretation, nonzero/error handling, mounts, native build flags and
port validation. These are NOT real-engine, rootless, SELinux-enforcement,
image-build, listener or named-volume persistence results. Neither Podman nor
Docker is installed in this sandbox. Full checkout/CI validation is pending.

Next integration must inject the selected engine into test_container.py, keep
both existing test assertions intact, use local fully qualified image tags and
the tested mount/port/pull adapters, and explicitly select Docker in Recovery
CI. The current Containerfile already uses docker.io/library/python:3.14-slim
and UID 1001; no production-image change is needed for those properties. Add
Podman usage documentation and execute the real two checks on Podman afterward.
README's Docker-only container instructions remain accurate for the still-
unwired Recovery module; update them with integration, not prematurely here.
HANDOVER's existing follow-up pointer is retitled generically to cover both
packaging and engine work. Application/runtime, container module, Containerfile,
CI, requirements, collector and every existing test stay unchanged in this
foundation commit. Bug 15 remains closed. No archive or Patch/ material.

## Login-guard helper alignment (2026-11-05)

Baseline: a19c52c71650c91594f91eaa3e1d256fce59608a on features/perplexity.
Run 41991526873 attempt 1 tested 1f31285bafb73b6dad7ee009ea4dab52de8342a7,
not the evidence commit. Reviewed evidence showed three Recovery failures at
headerless login and three mocked-browser setup errors through test_web.login.

Recovery login now sends Origin derived from its own client's base URL, preserving
scheme/authority/port and excluding any path. Redirect following is explicitly
false for the login POST. test_container imports this helper, so it needs no edit.
The shared test_web.login uses the same request-local policy; its two direct
login tests now supply same-origin headers too. The viewer-role denial also
checks its expected message so a guard rejection cannot masquerade as RBAC success.
The room-note recovery browser flow imports the shared helper; interception and
all browser/recovery assertions stay unchanged. No client-wide headers, request
monkeypatches, production-guard changes, skip markers or weakened tests are added.

Seven isolated helper contracts ran under Python 3.12.8 using extracted helper
functions and recording client doubles: original helpers 5 failed/2 passed;
candidate 7 passed. Cases cover two dynamic HTTP ports, HTTPS/path stripping,
IPv6, request-local headers and retained failure assertions. FastAPI is absent;
no real HTTP, browser, restart, container, full-suite or CI rerun was performed.
The doubled tests do not prove application integration success.

This is the requested helper/browser-setup scope, not migration of every direct
login caller behind the broader Python failures. Review and fix remaining direct
callers separately, retain missing/cross-origin rejection tests, finish proxy
usage documentation and rerun all five suites before acceptance. Bugs 20/21 stay
acceptance pending. README.md and HANDOVER.md were reviewed; the README test
summary and existing indexed link to this focused harness record remain accurate,
so no cosmetic edits are needed. Earlier historical records and CI artifacts are
preserved. No other branch, archive, Patch/ material or application change.

## Remaining Python login callers (2026-11-05)

Baseline: f6e69269c3d0b71250ff6c80a9b9fded0f4232b7 on features/perplexity.
Run 41994735806 attempt 1 tested dd882a5cbdf228b61aca443b731155d07ec8a0fb.
The reviewed run reports Browser, Recovery, Live and JavaScript success, but
Python still has ten failures: four reset-login combinations and six viewer
session cases blocked by headerless login. This is prior-run evidence, not a
result for the proposed changes.

The two password-reset /admin/login assertions now share request-local headers
derived from the client URL, excluding its path. Old-password rejection stays
401 and replacement-password acceptance stays 303. test_viewer_session_web.sign_in
uses the same origin derivation for /login and retains its 303 assertion and
viewer-cookie return value. No other requests gain headers. Session/socket,
CSRF, anonymous admission and missing/cross-origin guard assertions are unchanged.
Production code, prior helper fixes, workflows and existing skip behavior are
untouched; no skips, global monkeypatches or guard bypasses are added.

Nine isolated regressions ran under Python 3.12.8 with copied source call sites
and recording client doubles: original 6 failed/3 passed; candidate 9 passed.
They exercise HTTP, HTTPS/nondefault port/path stripping, IPv6, login payloads,
request-local headers, redirect flags, cookie return and preserved status checks.
They do not execute the reset transaction or WebSocket lifecycle. FastAPI is
unavailable; no real HTTP/WebSocket, full-suite, browser, recovery or CI rerun
was performed. Real integration validation is required before acceptance.

README.md and HANDOVER.md were reviewed. Their test overview and existing link
to this focused record need no cosmetic edits; current decisions and validation
limits are recorded here. Proxy-guide completion remains separate unfinished
work. Bugs 20/21 remain acceptance pending. Earlier handover text/manifests and
CI evidence are preserved; no other branch, archive or Patch/ material changes.
