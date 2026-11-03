## Passage modal/sidebar regressions

```sh
python -m pytest -q python/tests/test_destination_display_options.py python/tests/test_transition_templates.py python/tests/test_sidebar_appearance.py
node python/tests/test_map_transitions.js
node python/tests/test_sidebar_sections.js
node python/tests/test_viewer_refresh.js
python -m pytest -q python/tests/browser/test_passage_modal_layout.py
```

The route-body test checks current/saved reveal independence using stub dependencies;
it is not an HTTP authentication/CSRF test. The browser tests require local Playwright
Chromium. Manually verify footer visibility at your screen dimensions and zoom,
read-only inspection and popup-blocked fallback, and legend closure staying respected as peer panels
change. No passing browser or full-server result is implied by these commands.


