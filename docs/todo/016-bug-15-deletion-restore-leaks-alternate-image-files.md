### 15. Deletion/restore leaks alternate-image files
- [ ] Partial integration, step 2 of 4; validation and acceptance pending.
- Foundation: 901509e39acd1becec3ecddcd89372bfee63e954. Regression-first
  HTTP/CLI contracts: 71b83c049aa1205f3f7516584d5ea1ebb5a28da7.
- Step 2 registers original and alternate paths in the same write transaction
  before map/campaign deletion or HTTP restore removes their references. Old
  files are retained until explicit offline, reference-checked collection.
- Alternate replacement retirement is step 3; CLI serving ownership is step 4.
  Until then, stop ALL serving and standalone readers before collection.
- Preserve rollback state/bytes, active references and arbitrary untracked files.
  Original-image replacement and failed-new-image cleanup keep existing contracts.
- See [current evidence and limits](../handover/073-bug-15-route-cli-integration-2026-10-31.md)
  and [offline maintenance](../image-retirement.md). Existing/new regressions
  are preserved; no application pass or acceptance is inferred from source review.
