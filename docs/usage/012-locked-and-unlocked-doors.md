## Locked and unlocked doors

| Admin target | Single click | Double click |
|---|---|---|
| Locked arrow | No action | Unlock, fog unchanged |
| Unlocked arrow | Reveal destination | Lock, fog unchanged |
| Undiscovered secret arrow | No action | Discover as configured, fog unchanged |
| Normal portal Entry arrow | Reveal remote destination | No action |
| Exit-only hint | No action | No action |
| Door segment | Existing manual fog rules | No passage-state change |

Managed arrow singles wait 400 ms so a double gesture cannot first reveal.
State changes, another target, drag, wheel or blur cancel pending clicks. Portal
Entry sides have separate gesture identities. Secret portal state is independent
per Entry; Exit roles have no state. Configure secret outcomes in the wall editor.

Fog Undo affects reveal/hide history, not locks or discovery. Reset restores
authored states and hides secrets again; Restore/restart retains runtime state.
Saving/replacing walls clears runtime overrides for the replaced set. Export
contains authored states only. Locks never prevent a DM's manual reveal tools.
Locked door arrow color customizes the admin hint; viewers use the regular color.

