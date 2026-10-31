### 15. Deletion/restore leaks alternate-image files
- [ ] Four-stage implementation candidate; application validation/acceptance pending.
- Foundation: 901509e39acd1becec3ecddcd89372bfee63e954. Contracts:
  71b83c049aa1205f3f7516584d5ea1ebb5a28da7. Deletion/restore retirement:
  5e2f64a21062a9f73d5d8a7a38554f1b5024ac6a. Alternate retirement:
  e94304cbc2efb5f0dd5b88455f4826857c97e34c.
- Known old original/alternate paths are transactionally registered before
  deletion/restore and alternate replacement; files remain for offline collection.
- Step 4 coordinates normal POSIX CLI serving with collection through a shared
  lock held until worker-executor shutdown. Stop all readers for maintenance;
  direct/older/uncoordinated readers require explicit ownership or a full stop.
- Collection never scans arbitrary untracked files or runs during ordinary
  startup/context construction. Local POSIX/single-serving-process model only.
- Existing tests/workflows and original replacement/failed-new-file contracts
  remain unchanged. Compilation is not an application pass; keep unchecked.
- See [delivery/evidence and pending checks](../handover/073-bug-15-route-cli-integration-2026-10-31.md)
  and [offline maintenance](../image-retirement.md).
