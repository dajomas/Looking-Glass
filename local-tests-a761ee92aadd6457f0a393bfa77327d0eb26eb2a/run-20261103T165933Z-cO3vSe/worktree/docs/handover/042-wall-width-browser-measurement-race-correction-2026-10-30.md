## Wall-width browser measurement race correction (2026-10-30)

The failure in run 41029015169 occurred at the first four-pixel assertion in
`test_wall_width_is_screen_constant_and_survives_reload`, before zoom/reload.
The editor replaces wall paths using svg.innerHTML on state refresh, including
its scheduled post-artwork startup refresh. Chromium 134.0.6998.35 experiments
showed that an old detached path returns empty computed strokeWidth and CTM.a=1,
so parseFloat produces NaN despite a valid four-pixel replacement. Under rapid
path replacement, 150 locator-based samples returned NaN and 150 same-turn DOM
query/measurement samples did not. This establishes a reproducible failure
mechanism, not retrospective proof of the original CI sample's connectivity.

The test now queries the current path and measures CSS/CTM in one JavaScript
execution, using bounded five-second polling with the unchanged four-pixel
+/-0.01 tolerance at initial, zoomed and reloaded checkpoints. Missing paths,
nonfinite measurements and invalid scale cannot pass. Timeout diagnostics include
connectivity, raw CSS stroke width, CTM scale, calculated width and slider value.
Preference persistence and no-POST/page-error assertions remain; those checks
also run after reload. No application rendering code, fixed sleeps, test-level
retries, skips, tolerance relaxation, workflow or collector changes are included.
README.md was reviewed and remains accurate; no cosmetic README edit is needed.

The candidate helper passed actual Chromium 134 focused checks: static four-pixel
measurement, 100 samples during repeated SVG replacement, rejection of a 4.02px
stroke and rejection of a missing path with useful diagnostics. Helper syntax
parsed. These checks used a minimal SVG fixture, not the full checkout/editor.
The full modified repository browser test/suites and Python 3.14 CI have not been
executed by the assistant for this candidate; new CI acceptance remains required.

