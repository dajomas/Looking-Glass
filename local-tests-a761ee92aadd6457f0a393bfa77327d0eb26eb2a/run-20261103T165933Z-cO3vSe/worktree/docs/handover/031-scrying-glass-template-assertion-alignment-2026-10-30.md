## Scrying Glass template assertion alignment (2026-10-30)

The remaining failure in CI run 41014231894 against
`e13c1e7fbe220dad53391d8122a7cb409e037584` was the stale
`scrying-auto-2` assertion. The live admin map template references both
Scrying Glass assets with `scrying-prefix-3`. The test now checks the exact CSS
href and JavaScript src rather than searching for an obsolete generic token.
Script ordering, removed manual-check control, status markup, admin-only router
registration, viewer exclusion, CSRF and ownership assertions are unchanged.
No application template, script, stylesheet or runtime behavior changes.
Future intentional asset-version bumps must update these explicit expectations.
The live README and HANDOVER were reviewed; README needs no change for this
test-only correction. Tests have not been executed by the assistant for this
change; CI must validate both tests and assertions beyond the previous failure.
Historical validation statements above describe their preparation-time status;
subsequent reviewed CI run 41014231894 passed the original migration regression
and all five new migration tests, with four live tests passing. That prior run
does not establish that this new template assertion change passes.

