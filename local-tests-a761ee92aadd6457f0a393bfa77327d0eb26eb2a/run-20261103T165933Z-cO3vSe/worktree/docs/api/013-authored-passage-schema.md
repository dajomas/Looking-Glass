## Authored passage schema

Wall editor save/draft-export rows may have a seventh object:

```json
[200,70,200,130,"portal",true,{"pair":"p1","end":"a","sides":[{"role":"none"},{"role":"entry","kind":"secret","after":"locked_door","exit":0}]}]
```

The other element must have the same pair and end b; its side 0 must be Exit/Both.
Each pair has exactly two elements. Exit is always the 0/1 side index on the other
element: same-element/self routes cannot be encoded. Entry kinds are door,
locked_door, unlocked_door or secret; after is door/locked_door/unlocked_door.
Exit/None objects contain only role. Every Exit requires incoming routing, shared
Exits are valid, and at most one None is permitted per element. Invalid graphs
reject the entire save/export. Normal rows remain six fields; a secret door may
append `{"after":"locked_door"}`. Omission defaults to ordinary Door after discovery.

Admin map payload door_arrows add side, portal, exit_only and secret_origin;
portal_styles contains effective per-side appearance. No destination coordinates
are sent. These fields never enter viewer state. `portal` is accepted by wall-type
boundary settings. Looking Glass UVTT v2 round-trips the seventh field; v1 remains
supported. Downloaded/stored sources use authored configuration, never runtime.
Standard fallback represents portal elements as wall boundaries and loses routing.

Viewer default port is 5100; the older heading mentioning 6000 is superseded.

