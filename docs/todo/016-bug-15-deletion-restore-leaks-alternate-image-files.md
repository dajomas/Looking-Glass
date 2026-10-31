### 15. Deletion/restore leaks alternate-image files
- [ ] Partial integration, step 3 of 4; validation and acceptance pending.
- Foundation: 901509e39acd1becec3ecddcd89372bfee63e954. Regression-first
  HTTP/CLI contracts: 71b83c049aa1205f3f7516584d5ea1ebb5a28da7.
- Map/campaign deletion and HTTP restore retirement were delivered in
  5e2f64a21062a9f73d5d8a7a38554f1b5024ac6a. Original and alternate paths
  are registered before removal; old files remain for offline collection.
- Step 3 registers the previous alternate during replacement, inside its write
  transaction, without unlinking it. First uploads have no old path to retire.
- CLI serving ownership is step 4. Stop ALL serving and standalone readers
  before collection until it is delivered; uncoordinated readers still require
  a complete stop afterward. No arbitrary untracked files are scanned/adopted.
- Preserve rollback state/bytes and active references. Original-image replacement
  and failed-new-image cleanup keep existing contracts. Existing tests/workflows
  are unchanged; no application pass is inferred from compilation/source review.
- See [current evidence and limits](../handover/073-bug-15-route-cli-integration-2026-10-31.md)
  and [offline maintenance](../image-retirement.md). Keep unchecked pending acceptance.
