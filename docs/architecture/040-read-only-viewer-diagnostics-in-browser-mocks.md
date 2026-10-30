## Read-only viewer diagnostics in browser mocks

The browser helper handles the manager-only viewer-status GET with an explicit
empty-client response, never a wildcard success. Mutable map/action responses
remain owned by each fixture. The passage fixture owns its transitions response
rather than letting the generic empty auxiliary response shadow it. Standalone
UI-only pages have no map-metadata helper dependency. These are test boundaries,
not changes to production endpoints, authentication or permissions.


