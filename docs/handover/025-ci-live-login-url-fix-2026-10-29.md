## CI fix 1: live login URL predicate (2026-10-29)

Prepared against features/perplexity at
8bea73fbc49166034835eefddc9be24a362bd88d. The split root HANDOVER.md,
README.md, assistant-workflow section, CI setup section and live support helper
were read from that revision. Historical split content and its reconstruction
manifest remain unchanged; this is a new handover entry.

The user supplied results from Actions run 40946483639 at commit
27311d3a82f32c596236336f604a48a545bacf34: Python reported 964 cases, two
failure/error entries and zero skips; live reported four cases, four errors and
zero skips. Three displayed live errors fail in Session.login because its URL
predicate accesses .path on a string. The fourth traceback was not supplied.
These results were supplied by the user, not independently retrieved from Actions.

Scope: live_e2e/support.py imports urllib.parse.urlsplit inside Session.login
and parses the predicate argument before checking its path. Form interactions,
redirect condition, timeouts, credentials, production code and the live scenarios
are unchanged. A new top-level regression module extracts the actual login method
via AST without changing its body and executes it against a minimal page double.
The local import allows this focused test without importing Playwright or Pillow.
It checks seven URL-string cases and the original login form action sequence.

Validation executed with Python 3.12.8 using the exact baseline/candidate login
method bodies in temporary minimal Session source files and the proposed test:
- Baseline: seven failed with the URL string attribute error.
- Candidate: seven passed.
This is isolated method/predicate coverage, not execution of the full support
module, Playwright, application HTTP/WebSockets, Uvicorn or Python 3.14. No live
suite or full Python suite was run here. Real-browser acceptance remains pending
CI on the delivered revision; do not claim the live suite passes yet.

README links the focused regression command; root HANDOVER links this record.
No docs/testing.md rewrite is needed for the unchanged suite commands. No
migration, workflow, dependency, template or other CI failure is changed. The
fog-history ordering and stale scrying token failures remain separate follow-ups.

Prepared for an individually approved GitHub commit, not delivered at preparation.
Record the actual delivery SHA only after the write succeeds. No archive or Patch/
material is included. Existing split-manifest hashes refer only to the preserved
original handover pieces, not this added development record.
