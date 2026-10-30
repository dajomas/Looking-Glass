## Browser-test dependencies on Rocky Linux 10

Browser tooling belongs on development/CI hosts, not the running Looking Glass
service. Rocky Linux 10 is not an officially supported Playwright browser host;
its automatic dependency fallback invokes apt-get and must not be used there.
Use DNF for native packages and download the browser separately:

```sh
sudo dnf install -y nspr nss fontconfig dejavu-sans-fonts
python -m playwright install chromium
fc-match sans-serif
python -u python/tests/check_browser_environment.py
```

Run Python commands in the test virtual environment as the normal test user.
The package list is a starting point, not a compatibility guarantee. On supported
Ubuntu/Debian test hosts, Playwright's --with-deps installer remains appropriate.

The eee89c4 log now reaches a rendered-text assertion and reports missing
Fontconfig configuration. Verify /etc/fonts/fonts.conf, installed fonts and
FONTCONFIG_FILE/FONTCONFIG_PATH overrides. Reinstall Fontconfig if its installed
configuration is missing. See [testing.md](testing.md#fontconfig-and-rendered-text-failures)
for diagnosis and recovery commands. No system changes are performed by the
preflight or this patch, and GPU warnings alone do not establish a crash cause.


