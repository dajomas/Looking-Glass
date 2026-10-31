# Bug 15: accepted closure and validation limits (2026-10-31)

Repository: dajomas/Looking-Glass. Branch: features/perplexity.
Implementation and tested source: 000c46030807ab55b89e47a0f9e4f08da9dcb4de,
verified as live tip before preparing this documentation-only closure.

## Acceptance and current authority

At 22:10 CET on 2026-10-31, the user instructed: Push the Bug-15 fix to Github
and mark it finished if the failing tests are not related to the Bug-15 fix.
The fix was already delivered at the SHA above. Review of the supplied test log
and live test_container.py confirms the two observed errors are missing-Docker
fixture setup errors, before image build or application startup. They do not
exercise or demonstrate a failure of the Bug 15 retirement implementation.
The user's stated closure condition is met: record Bug 15 as accepted and closed
on that basis, while retaining the outstanding evidence and operational limits.

This record supersedes earlier open/candidate/acceptance-pending statements and
index labels in records 072/073 without rewriting their historical evidence.
Bugs 2, 13 and 14 remain accepted and closed. User acceptance is separate from
test execution, all-green CI status or unrestricted deployment approval.

## Delivered implementation

Map/campaign deletion and HTTP campaign restore register old original and
alternate paths transactionally before their references disappear. Alternate
replacement registers its previous path before the upsert; first uploads have
no old alternate. Retired files remain readable until explicit offline collection.
Collection checks both artwork tables, preserves active references, rejects unsafe
paths/symlinks, retries failed unlinks and acknowledges missing files idempotently.
No scan adopts arbitrary historical untracked artwork.

Normal POSIX CLI serving holds shared storage_use ownership before setup through
both listeners, asyncio.run and executor shutdown. Offline collection requires
exclusive ownership. There is no destructive collection during ordinary startup,
context construction or account CLI commands. Existing original-image replacement
and failed-new-file cleanup contracts are not redesigned.

Delivery commits:
- Foundation: 901509e39acd1becec3ecddcd89372bfee63e954.
- Regression contracts: 71b83c049aa1205f3f7516584d5ea1ebb5a28da7.
- Deletion/restore retirement: 5e2f64a21062a9f73d5d8a7a38554f1b5024ac6a.
- Alternate replacement: e94304cbc2efb5f0dd5b88455f4826857c97e34c.
- CLI ownership/documentation: 000c46030807ab55b89e47a0f9e4f08da9dcb4de.

## Execution evidence

These are user-executed application results, not assistant-executed runs. The
user explicitly confirmed that both the separately reported full Python/HTTP
run and the supplied broader testresults.txt run used the implementation SHA
above. The earlier focused command also printed that SHA and Python 3.14.7.
The broader log was reviewed by the assistant; no independent checkout/source
inventory verification or exact-source GitHub Actions evidence is claimed.

| Scope | Result |
|---|---|
| Focused nine-module run | 77 passed in 31.72s |
| Separate full Python/HTTP run | 1327 passed, 29 subtests passed in 156.86s |
| Broader Python including recovery | 1331 passed, 2 setup errors, 29 subtests passed in 187.27s |
| Browser / mocked HTTP | 172 passed in 148.24s |
| Live E2E | 18 passed in 100.56s |
| JavaScript | 28 distinct script entries; no consolidated exit inventory supplied |

The broader log explicitly shows all 37 new retirement cases passed: 14 service,
5 CLI and 18 HTTP cases. These overlap the focused/broader suite counts and
are not additional independent coverage. Subtests remain separate from ordinary
pytest case counts. Four non-container recovery cases passed: two migration-
interruption and two process-restart cases.

## Unrelated failures and remaining limits

The following two checks failed during built_image fixture setup because
shutil.which("docker") returned None:
- test_container_nonroot_listeners_templates_and_static_assets
- test_container_new_instance_preserves_named_volume_and_viewer_session

Source review at the tested SHA places that assertion at
python/tests/recovery/test_container.py:44, before docker version/build,
container creation or application assertions. The observed failure cause is
unavailable Docker, not Bug 15 behavior. This does not prove that the unexecuted
container assertions would pass: container-deployment coverage remains outstanding.
Do not relabel the errors as passes, add skips or weaken the unchanged CI/tests.
The overall broader run and five-suite validation are not recorded as all green.

The supplied run ends with gzip warnings that test-results/live-revocation,
test-results/migration-interruption and test-results/recovery directories were
ignored. Complete diagnostic packaging remains a separate unresolved concern;
the warnings do not invalidate recorded test passes or establish an artwork bug.
No manual stopped-maintenance result or reviewed all-green exact-SHA CI run was
supplied. Preserve those limits without reopening accepted Bug 15 solely for
missing evidence. A newly demonstrated implementation defect remains separately
actionable.

Supported operation remains one normal serving process on local POSIX storage
with reliable flock. Direct ASGI/server/service readers and older versions need
explicit coordination or a complete stop before collection. Network/distributed
locking, shared-cache multi-server use, external filesystem mutation and general
cancellation/crash/power-loss guarantees are outside the delivered safety model.
See docs/image-retirement.md and record 073 for details.

## Documentation-only closure

README.md and HANDOVER.md were reviewed live. README's implementation/maintenance
overview remains accurate and needs no cosmetic edit. Add one short current-
closure pointer to HANDOVER and check off only the individual Bug 15 backlog.
Keep records 072/073, all historical split manifests, code, assertions, tests,
workflows, migrations, dependencies and other bug statuses unchanged. No new
compilation, test, CI, browser, deployment or collection exercise was executed
for this closure preparation. No archive, Patch/ material, merge or other-branch
write. This records user acceptance and attributed evidence, not invented passes.
