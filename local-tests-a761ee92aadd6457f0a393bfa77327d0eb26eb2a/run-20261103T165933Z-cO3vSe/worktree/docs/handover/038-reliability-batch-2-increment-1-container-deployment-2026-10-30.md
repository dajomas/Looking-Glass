## Reliability batch 2 increment 1: container deployment (2026-10-30)

The first batch-2 increment adds two Docker-backed tests inside Recovery, not a
sixth check. CI explicitly sets LG_RUN_CONTAINER_TESTS=1 for the Recovery pytest
step. That same invocation reports both existing CLI cases and new container
cases in one JUnit file, so the common strict audit covers all of them. Local
container cases are opt-in and skipped otherwise; missing Docker after opting
in fails setup rather than skipping. Full local Recovery equivalence requires
the flag and a disposable Docker daemon/context with local bind-mount support.

The real Containerfile is built once per test session. Unique test-owned image,
container and named-volume names scope creation/removal; no shared-resource prune
is used. The first case checks non-root PID 1 uid 1001, both listener health
responses, both login templates and CSS/JS serving. The second seeds synthetic
accounts through non-root application code, creates campaign/map/walls/viewer
assignment/reveal via HTTP, validates exact revealed/hidden PNG pixels, then
stops/removes the first container and starts a new one with the same named volume.
The existing viewer cookie and map display version must still work; anonymous
access remains denied. Each case has isolated volume data and bounded clean
shutdown (zero exit required). A read-only temporary config provides small PNG
rendering; it invokes the real CLI with explicit config rather than testing the
default image CMD verbatim. Containerfile and runtime application are unchanged.

Docker version/build/command/inspect output and application logs are written
under test-results/container-build and test-results/container. Inspect logs have
synthetic test credentials only; review before publishing. getworkflow.sh already
collects every artifact and requires no update. Cleanup finalizers may not finish
if a workflow is forcibly cancelled or a daemon is unresponsive; manual cleanup
must target only the uniquely recorded resources. Image removal is best effort;
volume removal is checked. Docker-client timeouts do not guarantee daemon build
cancellation. This is Linux Docker coverage, not Podman/SELinux deployment proof.

Validation performed: new module passed Python syntax parsing; a synthetic Docker
port-binding structure produced the expected loopback URLs. No Docker engine,
image build, running container, actual deployment HTTP or full suite execution
was performed by the assistant. Acceptance of these two new cases is pending CI.
The preceding five-suite run 41020692166 at 6315be869139ee17536222795f4ae07e3d014c44
was reviewed green; that does not validate this increment.

Batch 2 remains incomplete: controlled migration interruption, file/database
failure injection and live access revocation are still planned next. Later
property/state-machine, delayed-response/restore and collector/runner harness
work also remains. README and docs/ci-tests.md now reflect the container scope,
local opt-in command, cleanup/evidence rules and validation limits.

