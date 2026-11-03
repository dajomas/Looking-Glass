## Campaign quick-navigation validation

From the repository root:

```sh
PYTHONPATH=python pytest python/tests/test_campaign_search.py python/tests/test_campaign_search_templates.py python/tests/test_campaign_search_web.py python/tests/test_campaign_readiness.py python/tests/test_campaign_readiness_templates.py python/tests/test_campaign_backup.py -q
node python/tests/test_campaign_quick_nav.js
```

Search service coverage includes category filters, unnamed notes, imported library,
Unicode casefold matching, multiword matching, literal SQL/wildcard punctuation, campaign
isolation, ranking/truncation, query/type limits, bounded snippets, URL escaping, deleted/
wrong-map target resolution and unchanged database state under query-only operation.
Template checks cover escaping, admin/viewer context gating and plain-text selected notes.
The Node DOM-stub regression covers request supersession/cancellation, stale responses,
text insertion, keyboard movement/Enter, shortcut input protection and focus restoration.
It is not a real-browser accessibility/layout test. HTTP tests verify manager/superadmin
access, viewer/other-admin rejection, JSON/HTML responses, validation, no-store, generic
inspection and unchanged campaign data. Missing FastAPI skips HTTP coverage.

Manual acceptance:
1. Keep a viewer open. Search and inspect results on several maps; ensure it never moves.
2. Test campaign, fog editor, wall editor, readiness and inspection contexts; confirm each
   search stays scoped to its campaign.
3. Exercise Ctrl/Command+K, arrows, Tab, Enter, Escape and focus restoration with a keyboard.
4. Confirm other modal dialogs and active text inputs are not interrupted.
5. Try network failure, rapid typing and changing result filters while requests are pending.
6. Confirm long results/snippets fit on narrow screens and full search works without JS.
7. Save pending editor drafts before following results; normal navigation may discard drafts.
8. Delete a result after searching and verify its old target is rejected rather than remapped.

