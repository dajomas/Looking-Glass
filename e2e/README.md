# End-to-end suite (Playwright, Chromium and Firefox)

Journeys through the real UI against a real `python/main.py serve` process with a
throwaway config and data directory on free loopback ports. Each test runs in both
Chromium and Firefox. Run it with:

```bash
tools/run_e2e.sh              # run, store, commit and push results ([skip ci])
tools/run_e2e.sh --no-push    # run and store only
tools/run_e2e.sh -k wall      # extra arguments go to pytest
E2E_HEADED=1 tools/run_e2e.sh --no-push
```

See [docs/testing.md](../docs/testing.md#end-to-end-suite) for requirements,
results and environment variables.

| File | Contents |
| --- | --- |
| `conftest.py` | Server subprocess, Chromium sandbox flag, failure artifacts |
| `support.py` | UI helpers (DM, player, pixel checks) and the `Table` scenario |
| `test_journeys.py` | Journeys: login, first-login password change, fog, wall drag, account, revocation |
