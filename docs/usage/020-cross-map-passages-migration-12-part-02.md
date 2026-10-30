The passage footer action is Travel… and its final confirmation says Travel to
[destination map]. It still uses saved configuration/session state, shows the
source/destination and arrival policy, and retains all server validation/approval
rules. Back to passage (or Escape) closes the confirmation without executing a trip
and reopens the same source form, retaining both pending field groups, their dirty
indicators and body scroll position. The prior focus is restored where available.
A new attempt performs a fresh preflight; cancelled requests are not reused. While
a trip request is in flight, cancellation is blocked to avoid implying the server
operation was stopped. Failed trips remain in the confirmation with an error.

The Show battle map choice now labels its actions Restore saved reveals,
Reset fog and show map, and Cancel. Reset permanently discards that map's reveal
history, restores wall-door locks and wall-passage discovery to authored states,
and shows the map fully covered. Fog Undo cannot undo this activation reset.
Cross-map endpoint session overrides remain separate and are not reset by it.
Restore still uses the existing checkpoint semantics; the labels do not change
activation behavior. Cancel still performs no activation or reset.


