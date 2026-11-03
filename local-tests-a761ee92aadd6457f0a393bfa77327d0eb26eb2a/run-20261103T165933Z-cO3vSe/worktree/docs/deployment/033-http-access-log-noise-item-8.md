## HTTP access-log noise (item 8)

By default, the built-in dual-portal server filters successful/informational HTTP
access records (100–399, including redirects and 304 responses) from
`uvicorn.access`. HTTP 400–599 access records remain visible at the configured
log level. Warnings/errors, unknown access-record formats and the separate
`uvicorn.error` / application loggers are not suppressed by this filter.
This affects logging output regardless of whether your deployment routes it to
stdout, stderr or a file; reverse-proxy access logs are unaffected.

For temporary full HTTP access logging, set in config.yaml and restart:

```yaml
server:
  access_log_success: true
```

The default is `false`; use actual YAML booleans, not quoted strings. Existing
configurations need no edit. `server.log_level` still applies: 4xx access records
normally have INFO severity, so choosing a WARNING log level can hide those too.
The filter targets Uvicorn's HTTP access tuples; WebSocket lifecycle messages on
other loggers remain unchanged. External Uvicorn launchers that bypass
`looking_glass.server.build` must configure their own logging policy.

