## Reduced-motion portal test synchronization (2026-10-30)

Run 41019420067 against 5f33869a133c4a601e9d66e9f3e84c2e93d1366f
passed all 14 new reliability cases (1,134 Python tests plus 29 subtests,
27 JavaScript scripts, seven live cases, two recovery cases) but the browser
suite reported 161 passed and one failure in the existing reduced-motion portal
style check. That test sampled computed CSS immediately after media emulation;
the assertion did not record which actual property differed. A synchronization
race is plausible, not a proven product defect or a proven harmless flake.

Only `test_admin_reduced_motion_is_bright_and_steady` changes: wait up to five
seconds for matchMedia to report reduced motion, require exactly two polygons,
then use Playwright locator CSS assertions on each polygon to wait for exact
animation-name none, yellow fill, black stroke and full opacity. The original
expected values and no-posts check are retained. Assertion diagnostics now
identify the property and observed CSS value. No fixed sleeps, whole-test
retries, skips, looser colors, stylesheet or runtime changes were introduced.
Other tests in the file are unchanged. README.md was reviewed and its CI overview
remains accurate. Workflow and getworkflow.sh need no changes.

The browser test and full suites were not executed by the assistant for this
correction; a new CI run must establish whether bounded CSS synchronization
resolves the intermittent failure. A persistent style mismatch must still fail
and be investigated using the richer assertion diagnostics.

