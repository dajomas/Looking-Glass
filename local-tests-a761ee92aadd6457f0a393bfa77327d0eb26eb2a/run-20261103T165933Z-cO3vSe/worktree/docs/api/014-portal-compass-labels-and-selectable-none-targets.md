## Portal compass labels and selectable None targets

Portal authoring uses compass names with map-top North, not visible side numbers.
This is presentation only: saved side/destination indices remain 0/1 and the API,
UVTT extension version and schema do not change. Choosing Unconfigured/None as an
Exit target converts it to Exit in the local popup, committed atomically with the
route on Apply. Existing Both targets preserve their Entry role; Entry-only targets
are rejected. Server complete-graph validation and all permissions remain unchanged.
See Passages.md.

