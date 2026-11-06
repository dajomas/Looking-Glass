# Bug 22: multipart CSRF type guard and HTTP regressions

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
