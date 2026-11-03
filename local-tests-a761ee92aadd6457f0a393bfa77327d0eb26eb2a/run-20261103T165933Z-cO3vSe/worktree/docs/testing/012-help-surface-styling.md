## Help surface styling

```sh
python -m pytest python/tests/test_help_background_styles.py -q
```

Three focused checks verify progressively lighter help surfaces, help-only CSS
selector scope and default-theme text/focus contrast. These are source-level
regressions, not browser layout tests. No additional test dependencies are used.

Manual check after a hard refresh: the collapsed Help control should be lighter
than Players/Fog/Walls. Expand Help and main topics to check their card surfaces;
expand Saved wall sources and its nested subsections to check the lighter nested
cards. Verify hover, Tab focus outlines, narrow layouts and independent toggles.

