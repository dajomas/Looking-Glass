# Deferred release-readiness follow-up

Recorded: 2026-11-06. Status: deferred; not started.
Working repository: dajomas/Looking-Glass, branch features/perplexity.

These are future acceptance and integration tasks, not new numbered bugs and
not a reopening of accepted findings 16–29. Preserve all existing closure and
evidence limits. Recording this plan does not authorize cleanup, branch writes,
merges or a release. Resume with live branch contents, not historical snapshots.

## 1. Acceptance-gap and deferred-work inventory

- [ ] Perform a read-only inventory of the current branch, handover records,
  release notes and known unfinished work. Start with the dedicated two-editor
  acceptance gap in [bug 27's accepted closure](../handover/093-bug-27-accepted-closure-2026-11-05.md).
- [ ] Separate completed validation, remaining acceptance checks, explicitly
  excluded scope and integration housekeeping. Do not infer exhaustive coverage
  from green suites or reopen accepted bugs merely because scope was limited.
- [ ] Record a concise action list with evidence references, completion criteria
  and an explicit decision for each deferred item: verify, accept the limitation,
  or separately scope follow-up work. Do not silently convert deferred scope
  into an approved implementation task.

## 2. Realistic DM/player acceptance session

- [ ] Use disposable or safely backed-up data and record the exact tested SHA,
  environment, participants/browser contexts and observed results.
- [ ] Exercise a connected workflow: import a map and assign walls, reveal/hide
  rooms, operate doors and cross-map passages, edit room notes from two editors,
  reconnect a viewer and restore a checkpoint.
- [ ] Cover bug 27's outstanding two-editor acceptance checks explicitly; record
  actual observations and any gaps rather than treating the general session as
  proof that every synchronization case was exercised.
- [ ] Retain acceptance evidence and classify any failures for separate review.
  This session supplements automated suites; it does not replace them.

## 3. Integration handoff and cleanup plan

- [ ] Review the intended integration diff, documentation consistency and file
  inventory; identify delivery files versus development/test-only artifacts.
- [ ] Reconfirm the user's earlier intended route through features/interim,
  then development and main. Inspect current refs before planning transfers;
  no branch head or merge readiness is assumed from old records.
- [ ] Prepare an explicit cleanup list for test results, temporary files and
  other non-essential material. The user plans to perform this cleanup manually.
  Preserve required tests, runtime files and useful evidence references; decide
  retention/archive treatment before removing evidence that documentation cites.
- [ ] Obtain fresh approval before any assistant cleanup/deletion, writes outside
  features/perplexity or merge. This checklist itself grants none of those actions.

## 4. Validate the cleaned integration candidate

- [ ] Identify the actual cleaned/integrated candidate SHA and review its diff;
  do not assume earlier green runs validate later cleanup or integration changes.
- [ ] Run the applicable focused regressions and full five-group validation on
  that exact candidate, including Python/HTTP, JavaScript, browser, live and
  recovery groups. Record real results, skips, failures and environment limits.
- [ ] Keep tested-source SHAs, CI run IDs and evidence-publication commits
  distinct. Recheck required imports, templates/static assets, documentation links
  and packaging after cleanup where affected.
- [ ] Resolve failures and outstanding acceptance decisions, then obtain an
  explicit integration/release decision. No automatic merge or release follows
  merely from passing tests.

## Resume and recordkeeping

Start with step 1 when this work is resumed. Update checkboxes only after the
corresponding work is actually completed and record evidence and remaining
limits. All four stages are currently deferred; no readiness review, acceptance
session, cleanup, branch integration or validation was performed to create this
checklist.

README.md and HANDOVER.md were reviewed and need no cosmetic changes for this
planning-only addition. TODO.md links this focused checklist. Historical audit,
closure records and reconstruction manifests are unchanged. No application or
test code changes, test execution, artifact deletion, archive or Patch/ material
are included. The requested documentation-only commit uses [skip ci]; actual
workflow skip status must not be assumed.
