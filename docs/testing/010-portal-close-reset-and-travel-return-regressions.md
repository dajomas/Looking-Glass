## Portal Close, Reset and Travel-return regressions

```sh
node python/tests/test_portal_modal_actions.js
node python/tests/test_map_transitions.js
python -m pytest -q python/tests/test_modal_action_templates.py
python -m pytest -q python/tests/browser/test_portal_apply.py python/tests/browser/test_travel_return.py
```

Test a clean Close, declined and accepted dirty Close/Escape, Apply followed by new
pending edits, paired-reset cancel/accept, and both travel return actions with both
save groups dirty. Verify no writes on return and a fresh preflight next time.
Use another tab to change a source after opening it; travel cancellation must not
silently rebase that editor's saved revision. Check Reset fog and show map only on
copied data and confirm the scope warning matches its existing effects. Node mocks
and template assertions are not substitutes for real-browser/live-server checks.

