## Browser tests

Install the additional browser-testing dependency and Chromium in the development
environment. Playwright is not included in requirements-dev.txt:

```sh
python -m pip install playwright
python -m playwright install chromium
python -m pytest -q python/tests/browser
```

The machine also needs the browser's platform libraries. Follow the locally
installed Playwright tooling's dependency diagnostics if Chromium cannot launch.
The included browser fixtures use mocked HTTP responses, not a live production
campaign. For a focused cross-map placement check:

```sh
python -m pytest -q python/tests/browser/test_map_transitions.py
```

