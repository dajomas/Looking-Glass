## Arrow-image and new-window inspection mock contracts

The real editor fetches door-arrows.png even when an isolated scenario has no
arrows. Raising an unexpected-route assertion there breaks pending requests and
can cause both test failures and teardown errors. The auxiliary helper now
handles exactly `/api/maps/{id}/door-arrows.png` for the current fixture map,
GET only, only when neither authored door arrows nor portal routes are present.
It returns a decodable transparent RGBA PNG at work resolution, falling back to
image resolution only when work dimensions are absent. Invalid dimensions,
other maps, writes, unrelated paths and authored imagery are not intercepted.
PNG bytes are cached for repeated identical dimensions. Tests decode the image
and verify dimensions/alpha, not merely its content-type header.

Inspect destination opens a new tab. Parent page.route handlers do not provide
a mock document for that new page's initial navigation. The regression now
registers a context route for the exact expected destination, checks its title
and URL, preserves parent dialog/no-write assertions, and closes/unroutes in
finally. The stub tests navigation/isolation, not destination editor rendering.
Unexpected destination URLs remain unmatched instead of silently succeeding.

Focused commands from repository root in the test environment:

```sh
python -m pytest -q python/tests/test_browser_fixture_support.py python/tests/test_inspection_fixture_contract.py
python -m pytest -v python/tests/browser/test_editor_controls.py
python -m pytest -v python/tests/browser/test_secondary_click.py
python -m pytest -v python/tests/browser/test_passage_modal_layout.py::test_inspection_does_not_activate_viewer
```

The zoom-2.5 screenshot threshold and its diagnostic capture are unchanged.
Neither this focused fix nor a focused test pass certifies the complete suite.
Patch/ distinguishes measured patch validation from supplied baseline results.

