# Travel approval wording

The travel confirmation adapts its approval control to the source passage's saved
current state. This is the effective state after applying session overrides; pending
editor selections are not used for travel.

| Source state | Checkbox label | Explanation |
|---|---|---|
| DM approval required, without secret/blocked restrictions | I approve this trip | Confirm that required checks or conditions have been resolved. |
| Secret or blocked | Allow this trip despite passage restrictions | Applies to this trip only. Does not discover, unblock, or change the passage. |
| Discovered and usable | No checkbox | No additional approval is required. |

Secret plus approval-required uses the restrictions label and lists both reasons.
The helper text identifies each applicable reason: Secret passage, Blocked passage,
and/or DM approval required. Admin-only visibility is not itself a travel restriction;
it still follows the passage's saved availability. The control is hidden and disabled
when no approval is needed, and the outgoing override flag is then false.

Each fresh preview clears the checkbox. You must deliberately approve each trip
that requires it; previous approvals do not carry over. Back to passage and Escape
return to the source form without saving the checkbox or executing travel.

Approval authorizes this attempt only. It does not discover a secret, unblock a
passage or persist a session override. Use Update session state for a lasting current
state change. It does not bypass missing/changed destinations, stale source/map
versions, permissions or the separate confirmation of a potentially large arrival
reveal. The server's existing needs_override and override behavior is unchanged.
The new wording is presentation only.

Inspect destination remains read-only and does not need travel approval. Travel
remains separate from normal Show to players and its fog restore/reset choices.
See [usage](usage.md), [passages](Passages.md) and [API](api.md) for the full workflows.

## Validation

```sh
node python/tests/test_travel_approval.js
python -m pytest -q python/tests/test_travel_approval_template.py
python -m pytest -q python/tests/browser/test_travel_approval.py
```

The Node checks cover all nine combinations of secret/discovered/admin visibility
and usable/blocked/approval availability, mixed reasons, repeated previews, and
hidden/required/disabled state. Template checks verify the helper-text accessibility
association. Browser tests require installed Playwright Chromium and mocked HTTP;
documented commands do not imply a passing real-browser or live-server result.
