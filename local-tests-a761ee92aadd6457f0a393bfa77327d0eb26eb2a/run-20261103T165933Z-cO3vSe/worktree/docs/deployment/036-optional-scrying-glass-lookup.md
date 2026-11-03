## Optional Scrying Glass lookup

A read-only Room notes lookup can query a matching Scrying Glass campaign/battle setup.
It is disabled by default. Configure the top-level scrying_glass block using the admin
origin (scheme/host/port), account, password environment variable and request timeout.
Set the secret in the Looking Glass service environment and restart. HTTPS is recommended;
TLS verification remains enabled. No migration or extra dependency is required. Existing
configuration files continue working without this block. See [Scrying Glass integration](scrying-glass.md)
for complete configuration, API contract, testing and reverse-proxy restrictions.

### Automatic verification and room checks

The manual Check Scrying Glass button has been removed. Selecting a room with a saved
name automatically verifies enabled configuration, login/catalog access and access to
one matching campaign before attempting the room lookup. Draft/unnamed selections do
not initiate verification. Disabled configuration hides the status and sends no upstream
request. Successful catalog verification is cached in memory for up to 60 seconds per
worker; failures back off for 30 seconds. Config/account/secret changes change cache
identity. Access revocations and catalog edits may take up to 60 seconds to appear.
There is no background poll: reselect a named room after expiry to retry/refresh, or
reload the page. Reload does not bypass the server's failure backoff. Restart clears
worker caches. Existing scrying_glass YAML settings remain unchanged. See the updated
[Scrying Glass guide](scrying-glass.md) for endpoint and cache details.
