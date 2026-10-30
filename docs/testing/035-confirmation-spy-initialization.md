## Confirmation spy initialization

Install browser instrumentation using an explicit initializer callback:

```python
page.evaluate("() => { window.confirmCalls = 0; window.confirm = () => { window.confirmCalls++; return false; }; }")
assert page.evaluate("window.confirmCalls") == 0
```

The initializer returns no function. The previous multi-statement string ended
with a function-valued assignment; evaluating it incremented the counter before
Apply. Check the counter baseline before the action, then verify the expected
request and check the counter again after completion. This fixes test
instrumentation rather than adding/removing a production confirmation dialog.
Exact payload assertions prevent a no-op Apply from incorrectly passing.

Run from the repository root in the test virtual environment:

```sh
python -m pytest -q python/tests/browser/test_campaign_batch_import.py::test_empty_upload_is_noop_and_apply_does_not_confirm
python -m pytest -q python/tests/browser/test_campaign_batch_import.py
```

The focused test also checks that empty submission performs no map uploads,
source uploads or assignments. The completed Apply payload must contain the
selected source ID, original scene index, alignment choice and use_pack_image=false.

Scope: this correction does not repair all failures in the supplied 2b81e59 run.
That run reports 529 Python passes, and browser results of 109 passed, 32 failed,
13 setup errors. Other failures include missing sidebar-help partials in mocked
Jinja loaders, editor image waits, modal pointer interception, saved-source status
expectations, progress timing and geometry/width assertions. Those remain outside
this focused patch. Do not interpret a batch-module pass as a full-suite pass.
See Patch/VALIDATION_BATCH_CONFIRM.md for the recorded execution and limitations.


