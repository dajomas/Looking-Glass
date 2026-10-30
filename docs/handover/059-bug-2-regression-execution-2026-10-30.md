# Bug 2 regression execution (2026-10-30)

Prepared against features/perplexity cdb7e0cee7be02f98ef957773fd9924f457291bf.

Correction to the conversational delivery report: e8d9ff791d1b1a20449326d50413c34b2ad82c7e delivered archive-aware duplication and its tests/documentation. The subsequent cdb7e0 commit changed only HANDOVER.md because the other submitted contents already existed. It does not mean the implementation is absent.

## Execution scope

The additive workflow .github/workflows/bug-2-regressions.yml runs on pushes to features/perplexity and manual dispatch. It selects every top-level test_room*.py module, campaign-backup modules, test_duplication.py and test_fog_snapshot_migration.py. This includes current save-context, archive/recovery HTTP, portability, backup and duplication contracts. It also executes every top-level test_room*.js script with Node 24. JavaScript JUnit cases count scripts, not nested Node assertions. Each script has a 120-second timeout. Python/HTTP failures do not prevent the JavaScript step after the Python execution step has been attempted.

Each execution retains the actual checkout SHA, environment, installed packages, Python selection, logs and two JUnit reports for 14 days. Missing/empty reports, failures, errors and skips fail the report gate. The original five-suite integration workflow, exclusions and test files are unchanged. This focused selection supplements rather than replaces full CI.

This change supplies execution automation, not new migration/reconciliation test cases. Migration 18 upgrade/rollback and reconciliation coverage expansion remain separate unfinished work. The existing fog snapshot migration regression is not a substitute for migration 18 validation.

## Validation and acceptance

README.md, HANDOVER.md, live integration workflow and current test inventory were reviewed. README.md remains accurate about the five-suite integration workflow and needs no cosmetic update. This focused record does not amend historical handover records or reconstruction manifests.

No application tests, pytest collection, JavaScript scripts, Chromium tests or GitHub Actions runs were executed or verified in this assistant session. The Python workspace has no checkout and cannot download dependencies/source; the available GitHub connector exposes no Actions run/artifact tools. A successful repository push is not execution evidence. No passing count, run ID or tested SHA is claimed.

After the push, inspect the new workflow's actual run and retained reports; verify the environment SHA matches the intended commit. Review individual failures and fix them without weakening contracts or adding skips. Also inspect all five existing integration jobs for the same source SHA. Browser, live Uvicorn, recovery/container, deployment and acceptance remain outside this focused job. Keep Bug 2 open and retain the development-state warning until the required evidence is reviewed.
