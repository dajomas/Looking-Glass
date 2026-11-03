## Browser regressions and isolated label paint checks (f4d60c3)

The existing secondary-click fixture separates read-only room-at POSTs from fog
mutations and still rejects unexpected mutation requests. The supplied local run
confirms those tests and both wall-width parameters pass; these fixes are already
in f4d60c3 and are not duplicated in this follow-up archive.

The portal-label test retains visible-text bounds, exact screen-relative padding,
font size, layer order, CSS fill, pointer behavior and non-scaling border checks.
A pixel two screen pixels from a rounded border is not an isolated measurement
of fill: glyph and edge rasterization may contribute. The exact source of the
reported (139,141,145) pixel has not been established from the supplied log.

`background_paint_sample` hides label text only during screenshot capture via
Playwright's screenshot `style` option. It samples a central 3x3 region of each
of four backgrounds away from their borders; every channel must remain <110.
It does not inject a replacement background in the positive test. Visible-text
geometry is measured before screenshot capture. This tests fill paint, not the
unmodified final composition at the former edge pixel; it is deliberately a
measurement-contract change rather than a production rendering fix.

Six negative-control cases set the screenshot-only fill to `none` or `#fff` at
zooms 0.5, 1 and 2.5. Every sampled pixel must fail the darkness criterion.
Tests verify normal text visibility and original fill return after capture.
Failure diagnostics include the isolated screenshot, sample values and an
unmodified screenshot. No pixel threshold or geometry tolerance is relaxed.

Validation: 13 portal-visibility tests passed in 7.14s under Python 3.12.8 and
pytest 8.3.5 in the assistant environment. This does not certify the full suite
or reproduce your Rocky Linux/Python 3.14 font/compositor setup.

Run from the configured test environment:

```bash
python -m pytest -v -ra python/tests/browser/test_portal_visibility.py
python -m pytest -v -ra python/tests/browser
bash runtests.sh
```

The module now contains 13 cases (7 existing + 6 negative controls); an otherwise
unchanged full browser collection should therefore grow from 155 to 161 cases.
See `Patch/VALIDATION.md` for supplied results and remaining limitations.

