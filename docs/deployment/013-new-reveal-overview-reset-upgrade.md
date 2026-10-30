## New-reveal overview reset upgrade

Apply the changed/new files to the supplied f1d837f source, which includes admin remote zoom. Stop both processes and back up code/data normally, extract at repository root, restart and reload viewer tabs so the versioned helper/display scripts and new state metadata are used together. No database migration, dependency or configuration change is required; admin tabs need no new gesture code.

Focus a viewer room locally and from admin, then reveal a second room: verify all visible areas are fitted/centered. Test a room inside unchanged overview bounds; hide/reveal exchange; Reveal all; Undo hide; repeated Reveal; colors, arrow flags and lock/unlock changes; and an old pending zoom response arriving after a reveal. Style/lock-only updates should preserve focus. See [testing](testing.md) for automated and manual checks. Rollback is the prior code version; there are no database changes to undo.

