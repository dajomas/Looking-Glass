## Python service and HTTP tests

Run the top-level suite, including HTTP tests but excluding browser tests:

```sh
python -m pytest -q python/tests --ignore=python/tests/browser
```

The HTTP tests require FastAPI and the installed project test dependencies. They
exercise application authentication, authorization and CSRF behavior. If an optional
module is skipped because a dependency is missing, install that dependency and rerun
it before claiming coverage of that integration.

For a focused cross-map passage check:

```sh
python -m pytest -q python/tests/test_map_transitions.py python/tests/test_transition_templates.py
python -m pytest -q python/tests/test_map_transitions_web.py
```

Other top-level tests cover fog, wall import/export, lock/discovery state, arrow
visibility, map activation, viewer zoom, cache identity and permission checks. Use
the full suite when changes affect shared behavior rather than testing a single
feature in isolation.

