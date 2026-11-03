## Collapsible sidebar help

```sh
python -m pytest python/tests/test_admin_sidebar_help.py -q
```

Seven regression cases render the real editor and help partial. They cover
single/multiple-map visibility, retained passage binding targets, eight main
help disclosures (seven for a single map), five nested source subsections,
initial closed state, absence of accordion names, revised wording and retained
live status/warning elements. Tests use the standard-library HTML parser and
existing Jinja/pytest dependencies; no new test package is required.

Browser smoke check: open Help, confirm all topics are initially closed, expand
several topics and nested source subsections independently, toggle control panels,
and verify Help stays open. Check pointer and Tab/Enter/Space interaction and a
narrow viewport. Reload to verify that every disclosure starts closed again.

