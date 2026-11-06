# Bug 22: multipart CSRF type guard and HTTP regressions

Current status: accepted and closed by user request on 2026-11-06. See
[accepted closure](#accepted-closure-2026-11-06). The preparation record below
is historical; its pending statements describe the implementation commit.

Date: 2026-11-06. Repository: dajomas/Looking-Glass.
Working branch: features/perplexity.
Reviewed baseline head: 492572c9bb09d1e9fb30c7daa7841859d4ab7553.

## Scope and decisions

verify_csrf now requires a string before calling constant_eq. Multipart file
fields named csrf_token follow the existing Forbidden path instead of reaching
.encode() on an UploadFile. The supplied value is annotated as object until the
string guard narrows it; the old assignment suppression is removed. Header
precedence, empty-header form fallback, safe-method bypass, token comparison,
authentication and the existing error message remain unchanged. No migration,
login-policy change, global constant_eq change or unrelated fix is included.

python/tests/test_csrf_multipart_web.py adds 20 parameterized HTTP cases using
the existing real-app/SQLite env fixture and login/csrf helpers. Both admin and
viewer accounts submit to the shared /account route. Cases cover missing,
empty, wrong, file-valued and matching-token-content file fields; valid form and
header tokens; valid header over file field; wrong header over valid form; and
empty-header fallback. A harmless upload forces multipart encoding in every
case. Rejections require 403, the CSRF message, an unchanged user-row snapshot
including password hash and a still-usable session. Success requires the
expected redirect, persisted profile change and unchanged other user fields.
Default TestClient exception propagation is retained; no assertions are skipped
or weakened. These are HTTP contracts, not browser or transport-security tests.

## Validation actually performed

The reconstructed baseline deps.py matched Git blob
137fe769a99de55b5a6a871b94d185a14de30987 before editing. The full candidate and
new HTTP test source syntax-compiled under Python 3.12.8. Their UTF-8 sizes are
3,203 and 3,131 bytes respectively, below the 25,000-byte rule.

Isolated execution extracted verify_csrf from the reconstructed baseline and
candidate with annotations removed and request/file doubles. Nine POST cases
and three safe-method cases were checked for each. The baseline raised
AttributeError on the non-string file double. All 12 candidate checks met their
contracts, including no form access with nonempty headers or safe methods.
These checks used the existing constant_eq algorithm; they did not parse real
multipart bodies or execute the full application. An initial sandbox harness
attempt used asyncio.run inside the notebook event loop and failed; the checks
were corrected to use await and rerun successfully. This was a harness error,
not an application result.

FastAPI is unavailable in the sandbox. The 20 prepared HTTP cases were NOT run;
no application, browser, live-server, recovery, full-suite or CI execution or
success is claimed. Run in the normal dependency environment:

```bash
cd python
../.venv/bin/python -m pytest -q tests/test_csrf_multipart_web.py
```

Review normal-runtime HTTP and broader regression evidence before acceptance.
Bug 22 stays open/acceptance pending; this commit does not close it. Parser-level
malformed-body exceptions, duplicate token policy and generic constant_eq input
hardening are outside this narrow fix.

## Documentation and delivery

README.md and HANDOVER.md were reviewed. README needs no cosmetic change for
this narrow rejection fix. HANDOVER.md adds a link to this focused record;
existing history and split manifests remain unchanged. No other branch,
archive or newly generated Patch/ material is included. GitHub delivery is
subject to exact approval; report its commit SHA only after a successful write.

## Accepted closure (2026-11-06)

The user explicitly requested finishing and closing bug 22 after reviewing the
implementation and published validation. Implementation commit:
`2e9894386d49310d994cb1ce0b40632e12d5e2f1`. This section supersedes the historical
acceptance-pending statements above. TODO.md marks bug 22 accepted and closed;
bug 24 is the only remaining open finding in the second audit. This is the
internal backlog item, not GitHub issue number 22.

### Reviewed CI evidence

GitHub Actions run `42177604548`, attempt 1, tested
`2e9894386d49310d994cb1ce0b40632e12d5e2f1` on features/perplexity. Evidence was
reviewed at `54625531e5f469d7c871f80f5ed06333cbdc31ee` under
`ci-results-42177604548-attempt-1/`. run.json reports overall success, all five
jobs successful and all report-validation steps successful. Reviewed JUnit
headers report zero failures/errors/skips: Python 1,746 entries, browser 172,
JavaScript 35 script-level cases, live 18 and recovery 6. The Python log explains
its count as 1,717 passed plus 29 passed subtests. Its reader-chunks/file-000082/
part-000008.txt explicitly lists all 20 test_csrf_multipart_web.py cases as PASSED
on both portals; part-000048.txt contains the Python final summary. This was a
review of stored metadata, report headers and selected log chunks, not an
independent rerun or an inspection of every diagnostic artifact.

### Local evidence

The user separately reported `.venv-test/bin/python -m pytest -q
python/tests/test_csrf_multipart_web.py`: 20 passed in 12.69 seconds. Treat this
as user-provided terminal evidence, separate from the published all-suite run.

Published all-suite local evidence is at commit
`47e912ca64818f860911b5cfb3e6ae9ad86f8d08` under
`local-tests-5462553/run-20261106T070532Z-Ax1tT1/`. workspace-identity.json records
requested, expected and actual source as
`54625531e5f469d7c871f80f5ed06333cbdc31ee`. environment.txt records a detached
sparse clone excluding uncommitted changes, Python 3.14.7 and WSL2/Linux; start
07:05:32Z and finish 07:13:35Z on 2026-11-06. summary.tsv reports test_exit=0 and
report_exit=0 for python, javascript, browser, live and recovery; exit-code.txt
is 0. The reviewed Python report-validation.log records 1,717 reported tests,
zero failed/error and zero skipped. No per-suite local counts beyond Python
are asserted: other local test entries and diagnostics were not individually
reviewed. CI and local tested revisions are distinct, as are their evidence
publication commits; do not present either publication commit as tested source.

### Acceptance limits and closure delivery

Accepted scope: non-string multipart CSRF token rejection before comparison,
controlled Forbidden response and unchanged rejection state, with valid token
and header-precedence behavior preserved. No CSRF bypass was established by the
original bug. Parser-level malformed bodies, duplicate token policy, generic
constant_eq input hardening and every browser/proxy topology remain outside
this acceptance. Broader green suites do not make those untested claims.

Closure changes documentation only; no application code, tests, migrations,
permissions or evidence artifacts are changed and no tests were rerun for this
closure. README.md, HANDOVER.md and release notes were reviewed. README.md and
the existing HANDOVER.md link remain accurate without cosmetic edits; release
notes and TODO.md are updated with this record. Historical audit and split
manifests remain unchanged. Delivery targets features/perplexity with commit
message `Close bug 22 and record accepted validation [skip ci]`; [skip ci] is
intentional for this documentation-only closure. No other branch, merge,
archive or Patch/ material is included. Report delivery only after write success.
