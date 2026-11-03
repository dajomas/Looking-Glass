# File-size rule: behavior-preserving splits (2026-11-03)

## Decision and scope

Any proposed repository change that increases a file's size and leaves its
resulting size greater than 25,000 bytes must include a behavior-preserving
split of that file in the same proposed commit.

- Measure file size in bytes, not characters or lines.
- The rule applies to newly created files and to existing files whose size
  increases, including files already above the threshold.
- Each resulting file must be no larger than 25,000 bytes. Moving oversized
  content into another oversized file does not satisfy the rule.
- Existing oversized files do not require a split solely because they exceed
  the threshold. The requirement is triggered when a proposed change increases
  their size.

## Implementation requirements

Split files along coherent responsibility boundaries without changing existing
functionality or externally observable behavior. Keep size-driven restructuring
separate from unrelated functional changes.

Identify every reference to, and consumer of, the original file. Update each
affected consumer to handle the split successfully, including imports, script
and stylesheet loading, templates, routes, build and packaging configuration,
tests, documentation links and tooling, as applicable.

Preserve loading and execution order, dependency relationships, initialization
behavior, shared state, public interfaces and resource paths. Dividing a file
into smaller files is insufficient without integrating those files into all
affected execution and delivery paths.

Include the split and all necessary consumer, reference, test and documentation
updates in the same proposed commit, subject to the normal approval workflow.

## Validation and exceptions

Use appropriate checks and regression tests to verify that the resulting files
remain within the size limit and that affected functionality and consumers
continue to work without behavior changes.

Record actual validation performed, checks not executed, known limitations and
unfinished work in the relevant handover record. Do not claim tests passed or
functional equivalence was established without supporting executed validation.

If a file cannot reasonably be split while preserving behavior, such as an
indivisible binary asset or externally mandated format, document the conflict
and obtain explicit approval for an exception before committing it.

## Documentation change and evidence limits

This record adds the workflow rule; HANDOVER.md links it under Current repository
directives. Existing historical records and split manifests are unchanged.
README.md was reviewed and needs no change for this documentation-only update.

The live README.md, HANDOVER.md, introduction, authority and assistant-workflow
records and handover directory listing were read before preparing this change.
No application files were split, no application behavior was changed, and no
application tests or CI were run. No automated size enforcement was added and
no repository-wide size audit was performed. Future changes must apply and
validate the rule; this record does not claim those future checks have run.
