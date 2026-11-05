# Door-arrow fixture alignment (2026-11-05)

## Scope

Repository: dajomas/Looking-Glass. Branch: features/perplexity.
This is a test-fixture correction only, not a production change or bug closure.

Bug 25 routed rejected-action refreshes through readState. The source-extracted
onTap/performMapTap fixture still supplied LGApi.get and applyState but omitted
readState. The handler swallowed that missing-helper error while preserving the
original mutation error, leaving notices empty; the fixture then crashed reading
notices[0].refreshed.

Published local evidence for d11f58d74c1b3b10b6324ff78fa9df63a1d35a31 at
abc99914bd6df193f151d5149d2570c4f960b6c8, directory
local-tests-d11f58d/run-20261105T151520Z-rd7W75, reported this as the sole failing
JavaScript script (30/31 scripts passed). The overall run remained exit 1.
That historical evidence must not be relabeled as a passing run after this fix.

## Change

python/tests/test_door_arrow_click.js provides a mocked readState boundary that
awaits its mocked map GET and installs the returned payload through applyState.
It does not duplicate or bypass production request-generation logic: that logic
is covered by the separate full-editor ordering tests.

All existing assertions remain. Additional assertions require exactly one GET
to /api/maps/1, exactly one refreshed-state installation, and preservation of the
original stale error message after the rejected arrow action. The existing
one-POST assertion continues to reject a normal reveal/hide fallback.

## Executed validation and limits

Sandbox Node.js v20.20.1, isolated temporary layout using onTap/performMapTap
handlers copied from the live editor tool result, not a complete checkout.
The original test text matched Git blob 3ac2fb82167a7f661354000ceba82c5a67164460.

- Original fixture: exit 1, reproducing the published undefined/refreshed error.
- Corrected fixture: exit 0, Door arrow tap handler tests passed.
- Corrected fixture node --check via standard input: exit 0.
- Temporary handler mutation omitting refresh: corrected fixture failed.
- Temporary handler mutation replacing the original error: corrected fixture failed.

Neither mutation is proposed for delivery. These checks show that assertions
still detect missing refresh and lost original errors; they are not browser,
HTTP, full-editor, full-JavaScript-suite or CI validation. The other 30 scripts
and other suites were not rerun for this fixture-only candidate. The fixture is
2,543 UTF-8 bytes; all proposed files are below 25,000 bytes.

README.md was reviewed and remains accurate without changes to setup or commands.
HANDOVER.md links this focused record. The earlier fixture-follow-up statements
in record 089 are historical; this record documents the proposed correction.
No application files, published evidence, backlog statuses, migrations, deletion
or archive-only Patch material are changed. Bugs 25/26 remain pending acceptance.

## Remaining work

Approve and deliver the fixture correction, then run from the repository root:

```bash
node python/tests/test_door_arrow_click.js
```

Rerun and publish commit-scoped JavaScript/full local evidence as appropriate
before claiming the overall validation gate is green or closing bugs 25/26.
