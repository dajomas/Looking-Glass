## Reliability batch 3 increment 2: delayed viewer responses (2026-10-30)

The user subsequently ran the committed JavaScript-runner module in their real
checkout with .venv-test: nine cases passed in 3.41 seconds. This adds local
checkout validation, not a reviewed full-CI result. The user then excluded further
collector harness work from workflow testing and requested application tests.
No collector tests, prompt changes or collector documentation changes are part
of this increment.

Added seven cases in `python/tests/browser/test_viewer_delayed_responses.py`:
old state headers, old JSON consumption, late images after a same-map update,
a map switch or a blank scene, readiness while the current image is delayed,
and failed delayed-image retry without changing the requested version or reloading.
The standalone page loads the real viewer_display.js, pan_zoom.js and
viewer_area_zoom.js. Route-held HTTP payloads and a test WebSocket driver select
response order. Native fetch/body parsing/image requests/decoding remain in
Chromium; test wrappers only gate JSON delivery or record completion/status.
Synthetic PNG fixtures contain an exact colored left region and black right
region, not server-rendered fog or real campaign artwork.

Bounded waits synchronize startup and barriers. Post-release completion markers
allow stale continuations to run before assertions. Tests check installed image
URLs, map titles, stage/waiting visibility, image pixel samples and emitted ready
versions, including blank. The loading case rejects premature readiness; the
failure case requires Display failed followed by recovery without page reload.
Unexpected HTTP writes/requests and uncaught page errors fail the fixture.
Pending HTTP routes are aborted during teardown and each browser context closes.
There are no fixed sleeps used to select a race, runtime viewer changes, new
requirements, workflow or collector changes. Existing Browser / mocked HTTP
suite discovery includes the module, not the Live Uvicorn job.

Validation remains intentionally limited: the draft passed Python syntax parsing,
and the live browser fixture was reviewed for integration. None of these seven
Chromium cases, the full browser/application suites or hosted Python 3.14 CI has
been executed by the assistant. This is a test candidate requiring execution and
possible harness corrections, not a passing-run claim. No new runtime defect is
asserted from an unexecuted draft. Prior test results do not validate these cases.
README.md was reviewed and remains accurate; the focused command is
python -m pytest -q python/tests/browser/test_viewer_delayed_responses.py.

Coverage is client-side response ordering/readiness with synthetic HTTP/WS input,
not live-server delivery, server authorization, actual fog generation, all timing
races or a mutation-sensitivity proof. Live delayed-response and restore/checkpoint
propagation, post-image-store transaction cleanup, controlled restore/duplication
interruption and broader property/security/fault coverage remain separate work.

