### 1. Feathered fog exposes hidden artwork
- [x] Accepted and closed on 2026-11-22 by explicit user instruction; see [accepted closure and evidence limits](../handover/102-bugs-1-3-12-accepted-closure-and-acceptance-findings-2026-11-22.md). The delivery and pending-acceptance notes below are historical. A 2–3 px doorway sliver found in manual acceptance is tracked separately as bug 30.
- [x] Complete; delivered on `features/perplexity`.
- Fix commit: `253b33ddae49d403a3985bf99135ce07226e95e4`.
- Validation: 15 new regression cases and 246 related service tests passed on
  Python 3.14.4. HTTP/browser/live-viewer/JPEG/WebP visual checks remain
  outstanding; the broader non-HTTP suite was not fully green (see HANDOVER.md).
- Problem: `services/fog.py` blurs the reveal mask into hidden-room artwork.
- Solution: feather inward, clip permitted coverage, prevent dilation into hidden
  interiors, and invalidate unsafe old composites through a new cache identity.
- Test: adjacent-room pixels remain hidden with default feathering and scaling;
  revealed rooms and bounding walls still render.

