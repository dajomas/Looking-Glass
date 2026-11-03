## Viewer portal and discovered-secret arrow exceptions

When **Show door arrows (viewer)** is unchecked, two indented controls appear:

- **Show portal arrows (viewer)**: show eligible portal entry/Both arrows, including discovered secret portal entries.
- **Show secret arrows (viewer)**: show eligible arrows with a secret origin after discovery, including secret-origin portal entries.

The categories form a union: either matching option is sufficient. An entry whose current state is `secret` is always hidden from players, regardless of all three toggles. Ordinary doors remain hidden when the main toggle is off. Existing revealed-area, blocking-wall, source-side, and doors-split-areas rules still apply; these options never reveal fog or display admin-only exit hints.

The main viewer toggle retains its previous all-eligible-arrows behavior when enabled. Exception choices are saved per map, retained while the main toggle is on, and default to off for both existing and new maps. The admin arrow toggle is independent. Changes are saved immediately and notify connected viewers.


