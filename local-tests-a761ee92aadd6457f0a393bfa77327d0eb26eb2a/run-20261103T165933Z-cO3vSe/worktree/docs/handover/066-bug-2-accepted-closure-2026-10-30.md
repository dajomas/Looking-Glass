# Bug 2: accepted closure and documentation reconciliation (2026-10-30)

Documentation baseline: features/perplexity
b376e67407a739342669459b53dbf31ec6b609ff.

## Current status and authority

The user explicitly accepted Bug 2 on 2026-10-30 at 22:37 CET and subsequently
requested closure documentation. Record the backlog item as closed by that user
acceptance. Earlier dated records and index labels saying acceptance pending or
warning about intermediate implementations retain their historical context; they
are not the current acceptance status. This record supersedes those pending-status
statements, not their evidence or their still-applicable operational limitations.

User acceptance is not a new automated test result, a blanket deployment approval,
or evidence that the disposable schema-17 upgrade/recovery checklist ran. No
execution of that exact exercise is recorded here. It remains an outstanding
validation item. Do not infer a waiver or an executed pass from backlog closure.
Use stopped full database/image backups and isolated disposable storage for
upgrade testing; never downgrade an upgraded database in place.

## Delivered behavior

Geometry reconciliation retains exact saved room names and Markdown before
releasing invalid active assignments and imported-name reservations. Retained
archives stay detached even if geometry returns. Imported library originals are
not substitutes for custom saved edits. Read-time reconciliation can archive and
detach; it is not automatic recovery.

Management-only listing/recovery and a dedicated Retained notes workspace provide
deliberate selection and confirmation. Recovery validates map incarnation, effective
boundaries, note generation, area identity and target revision. Replacing a nonempty
target requires explicit confirmation and archives its old content first. The
source archive remains available. Ordinary editor saves also require the current
selection context; an old draft must not be automatically restamped. Note-only
recovery does not change fog, the active map or viewer output.

Campaign ZIP backup/restore and clean duplication include detached archives and
exact content, remap current ownership/local IDs and preserve historical provenance.
Copies retain normal clean-copy behavior. Owning map/campaign deletion cascades
archives; retention is not protection against intentional deletion or lost backups.

## Evidence boundaries

The historical coverage record 062 reports five-suite success for source
d5fea76382118277a16ac0c2fd15a7e67508bfe8 in run 41124059137, attempt 1. That
result does not establish success for later source or dependency changes. Record
064 reports run 41128592368 against 8652625c4be6a322edd322807cc8598f97cda522:
four jobs succeeded; browser execution reported 171 passes and one portal
reduced-motion assertion failure, while all three retained-note recovery UI
tests passed. Its subsequent assertion synchronization correction was recorded
as source review only. These are attributed historical results, not a newly
reviewed all-green result for this documentation baseline.

No application tests, CI run, browser session, migration or manual upgrade
exercise were executed as part of this closure. The checklist in record 062
remains a procedure, not proof of execution. Any later evidence review must
record the actual tested SHA, run/attempt and results independently of acceptance.

## Documentation changes and preservation

Close only Bug 2's individual TODO section. Add this current-status pointer to
HANDOVER.md without rewriting earlier records. Correct current room-note recovery
and backup status, usage retention/name-availability guidance and ordinary-save
API context/error documentation. README.md was reviewed: its existing room-note,
backup and duplication descriptions remain accurate, so no cosmetic edit is made.

Original TODO, handover, API and usage split manifests remain untouched. They
describe historical snapshots; edited current sections intentionally differ from
their split-time hashes. Reconstruct those snapshots from their Git history,
not by claiming the semantically updated guide still matches the old manifest.
The lossless split was verified before these semantic corrections. No runtime
code, tests, dependencies, migrations or archive-only Patch/ files change.

Remaining work is validation/evidence review as described above and separate
backlog items, starting with Bug 13 if selected. Do not describe those items as
implemented or accepted by this documentation-only closure.
