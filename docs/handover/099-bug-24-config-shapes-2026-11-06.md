# Bug 24: configuration shape validation candidate

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
