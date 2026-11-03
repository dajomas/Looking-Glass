## Process model

`python/main.py` → `looking_glass.cli` → `looking_glass.server.serve()` runs
**two uvicorn servers in a single asyncio event loop**:

```
                 ┌──────────── one Python process ────────────┐
 DM browser ───► │ :5000  admin FastAPI app  ─┐               │
                 │                            ├─ AppContext ──┼─► SQLite (data/looking_glass.db)
 Player screen ─►│ :5100  viewer FastAPI app ─┘  (db, fog,     │   map images (data/maps/)
       ▲         │                               hub, settings)│   render cache (data/cache/)
       └── WS ───┤ EventHub: admin action → viewer WebSockets  │
                 └─────────────────────────────────────────────┘
```

Both apps share one `AppContext`, so an admin action can push a `refresh`
event to connected viewer WebSockets directly, with no broker. Signal handling
is centralised so Ctrl+C / SIGTERM stops both servers cleanly.

