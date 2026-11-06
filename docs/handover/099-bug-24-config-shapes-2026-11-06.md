# Bug 24: configuration shape validation candidate

Current status: accepted and closed by user request on 2026-11-06. See
[accepted closure](#accepted-closure-2026-11-06). The preparation record below
is historical; pending statements describe the implementation preparation.

Date: 2026-11-06. Repository: dajomas/Looking-Glass.
Working branch: features/perplexity. Bug 24 remains open/acceptance pending.

## Scope and decisions

The user approved structure validation, not numeric-range or leaf-type policy.
load_settings validates YAML and programmatic overrides before merging them.
Supplied server, storage, security, fog, viewer and scrying_glass sections must
be mappings. Errors name the configuration file or overrides and the invalid
section, without echoing submitted values. File structure is checked before
environment assignment; overrides are validated before environment conversion
and merged last, retaining precedence. Explicit-file opening remains ahead of
override validation, preserving bug 23's missing-file failure behavior.

Empty/comment-only documents and YAML null (all parsed as None) retain defaults.
Other false-like roots, including false, 0, empty string and empty list, no longer
silently request defaults. None programmatic overrides still mean no overrides.
Mapping inputs, including UserDict sections, deep-merge; unknown extension keys
and leaf values are not restricted. Defaults and caller overrides are not
mutated by loading. Direct Settings construction is not a new validation gate.
Existing Scrying Glass options validation remains in place. No CLI redesign,
migration, numeric-range validation, strict unknown-key schema or bug closure.

## Tests and validation actually performed

New test_config_shapes.py has 182 parameterized loader cases: all three YAML
selection routes, eight invalid roots, six invalid values for each known section,
programmatic shape rejection, empty/null document compatibility, empty mappings,
partial merge/precedence/extensions, UserDict and missing-file precedence.
New test_config_shapes_cli.py adds eight subprocess list-users cases using
--config or LG_CONFIG, requiring a named shape error and no storage/bootstrap
writes. Existing bug 23 tests are unchanged and must be rerun in the normal
runtime alongside these tests.

The reconstructed baseline config.py matched Git blob
5a45698226ecc298755a4c60c3ea8d185f057208. Full candidate and both test files
syntax-compiled under Python 3.12.8. Candidate UTF-8 sizes: config.py 6,073 bytes,
loader tests 4,358 bytes and CLI tests 1,619 bytes, below the 25,000-byte rule.
In an isolated temporary package, pytest ran the new loader tests against the
reconstructed baseline and candidate. Final runs used the extracted live Scrying
Glass options function and supporting declarations/imports, not the full service
or repository package: baseline 177 failed, 5 passed; candidate 182 passed.
An earlier harness run used a no-op options double and produced the same totals;
it was replaced with extracted real options logic before the final rerun.
These are isolated loader results, not full repository integration results.

The eight CLI cases, existing bug 23 suite, full application, browser, live,
recovery and CI suites were NOT run here. Normal runtime/FastAPI is unavailable
in the sandbox. Run in the project environment:

```bash
.venv-test/bin/python -m pytest -q python/tests/test_config_shapes.py python/tests/test_config_shapes_cli.py python/tests/test_config_selection.py python/tests/test_config_selection_cli.py
```

Then review full CI/local evidence and obtain acceptance before closure.
No successful CLI no-bootstrap or deployment result is claimed from static CLI
ordering review or syntax compilation. Cyclic YAML, arbitrary leaf types/ranges
and direct Settings construction remain outside this agreed boundary.

## Documentation and delivery

Live README.md and HANDOVER.md were reviewed before changes. README does not
specify detailed loader shape rules and needs no cosmetic update. HANDOVER.md
links this focused record; historical records and split manifests are unchanged.
This proposed implementation/test/documentation commit intentionally has no
[skip ci]. Delivery requires exact content approval and a successful GitHub
write; report the actual SHA only afterward. No other branch, merge, archive
or Patch/ material is included. TODO.md status stays open.

## Accepted closure (2026-11-06)

The user requested finishing and closing bug 24 after focused, full local and
CI validation. Implementation commit:
`b165a44ca915b04f0a5196373ddece904b558a8c`. This acceptance supersedes the pending
statements in the preserved preparation record above. TODO.md marks bug 24
accepted and closed; all 14 findings 16–29 from the second audit are now closed.
This closes the internal backlog item, not GitHub issue number 24, and does not
claim that no undiscovered defects or documented acceptance gaps remain.

### Focused and full local evidence

The user reported the four-file configuration command above completed with
206 passed in 8.37 seconds: 182 new loader cases, eight new CLI no-bootstrap
cases and 16 existing bug 23 selection/CLI cases. The terminal excerpt alone
did not include a checkout SHA; keep this separate from the published run.

Full local evidence was reviewed at publication commit
`82fa18d62c35912793c04a9d20b294b73f17317e` under
`local-tests-b165a44/run-20261106T080205Z-WGRA5c/`. workspace-identity.json records
requested, expected and actual source as the implementation SHA above.
environment.txt records a detached sparse clone excluding uncommitted changes,
Python 3.14.7 and WSL2/Linux, start 08:02:05Z and finish 08:10:38Z on 2026-11-06.
summary.tsv reports test_exit=0 and report_exit=0 for all five groups and overall
exit-code.txt is 0. All five report-validation.log files were read: Python 1,907,
JavaScript 35 scripts, browser 172, live 18 and recovery 6, each with zero reported
failures/errors/skips. These are validator-reported totals, not an independent
recount of every local test entry. Local diagnostics were not exhaustively read.

### Reviewed CI evidence

GitHub Actions run `42184320542`, attempt 1, tested the same implementation SHA
on features/perplexity. Evidence was reviewed at publication commit
`713cac8e24edce8e16ff843ec0f4af9d58fc8edb` under
`ci-results-42184320542-attempt-1/`. run.json records overall success, all five
jobs successful and their report-validation steps successful. JUnit headers
report zero failures/errors/skips: Python 1,936 entries, JavaScript 35 script
cases, browser 172, live 18 and recovery 6. Python pytest's final summary in
reader-chunks/file-000082/part-000054.txt explains its count: 1,907 passed plus
29 passed subtests in 204.81 seconds. Selected chunks 10–12 explicitly show
passing loader rejection/compatibility cases and all eight CLI no-bootstrap
cases. This was metadata, header and selected-log review, not a rerun or an
inspection of every artifact. Publication commits are not tested source.

### Accepted scope, limitations and delivery

Acceptance covers the supplied top-level and known-section mapping boundary,
actionable source/section diagnostics, CLI rejection before bootstrap writes,
valid partial merge/precedence/extensions, preserved empty/null documents and
bug 23 regressions. It does not add numeric-range or arbitrary leaf-type checks,
a strict unknown-key schema, cyclic-YAML handling, direct Settings validation,
every platform/proxy topology or a guarantee against undiscovered defects.

This closure changes documentation/status only. No code, tests, migrations,
evidence artifacts or historical audit/manifests are changed. No tests were
rerun for closure and no new test success is claimed for the closure commit.
README.md and HANDOVER.md were read: README needs no cosmetic change; its
existing handover index still links this preparation/evidence record, now with
an explicit current-status notice and closure section. Release notes now record
the accepted behavior and remove the obsolete implication that bug 24 is still
outstanding. TODO.md records the completed second audit. No other bug's status
or acceptance limits are changed.

Delivery targets features/perplexity with message
`Close bug 24 and record accepted validation [skip ci]`. The skip marker is
intentional for documentation only, not proof of actual workflow skip status.
No other branch, merge, deletion, archive or Patch/ material is included.
Report the actual closure SHA only after the approved write succeeds.
