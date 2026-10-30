## Rocky Linux 10 / WSL browser preflight

Playwright's automatic dependency installer does not support Rocky Linux 10.
Do not run `install-deps` or `install --with-deps` there: the fallback calls
Ubuntu's apt-get. On supported Ubuntu/Debian hosts, the --with-deps installer
can be used. On Rocky, provision dependencies with DNF and download Chromium
as the normal test user, in the test virtual environment:

```sh
sudo dnf install -y nspr nss fontconfig dejavu-sans-fonts
python -m playwright install chromium
fc-match sans-serif
python -u python/tests/check_browser_environment.py
```

This is a starting dependency set, not a full native compatibility guarantee.
Rocky is not an officially supported Playwright browser host. Resolve any
remaining missing shared library using `dnf provides '*/NAME.so'` and inspect
the trusted downloaded executable with ldd. Do not install Ubuntu packages or
create arbitrary library symlinks on Rocky.

### Fontconfig and rendered-text failures

The supplied eee89c4 run reports 521 Python passes. Its browser preflight reaches
page creation, HTTP navigation and set_content, but fails the rendered text
assertion. Browser stderr includes “Fontconfig error: Cannot load default config
file” and Vulkan/EGL errors; the browser is then closed normally in the cleanup
block. This is not the original missing-libnspr4 launch failure. The exact value
returned by inner_text was not recorded in that old run, so do not infer it.

The updated preflight records both DOM text_content and rendered inner_text,
FONTCONFIG_FILE/FONTCONFIG_PATH overrides, and bounded fc-match output. It keeps
both DOM and rendered-text checks strict: replacing inner_text with text_content
alone would mask a rendering problem. A mismatch still fails the preflight.
Fontconfig warnings are evidence to investigate, not proof of the only cause.

Verify installed configuration, font availability and environment overrides:

```sh
rpm -q fontconfig dejavu-sans-fonts
rpm -V fontconfig
ls -l /etc/fonts/fonts.conf
fc-match sans-serif
printenv FONTCONFIG_FILE FONTCONFIG_PATH
```

If configuration files are missing from an installed Fontconfig package, restore
them with `sudo dnf reinstall fontconfig`. Investigate custom environment paths
before changing them. If overrides are accidental, compare a one-command run
using system defaults without changing the parent shell:

```sh
env -u FONTCONFIG_FILE -u FONTCONFIG_PATH fc-match sans-serif
env -u FONTCONFIG_FILE -u FONTCONFIG_PATH python -u python/tests/check_browser_environment.py
```

Do not disable SELinux or change GPU flags based solely on warning text. The
Vulkan/GPU messages are not proven to cause this failure. Use pw:browser process
logs and the explicit DOM/rendered values to diagnose further if font setup is
healthy. Native Rocky compatibility remains best-effort; a supported container
userland is an alternative, with matching Playwright image/package versions and
a Python runtime meeting the project's requirements.

### Running and interpreting the checks

```sh
python -u python/tests/check_browser_environment.py
bash runtests.sh
```

The preflight starts a temporary loopback HTTP server; it needs no production
server or campaign data. It uses the current fixtures' headless/no-sandbox test
settings, not a production sandbox policy. Its parent imposes a 45-second timeout;
use --timeout to adjust. Font diagnostics have a separate five-second timeout.

runtests.sh logs preflight output to test-results/browser-preflight.log. If it
fails, browser.log says NOT RUN and the entire run returns nonzero even after
log packaging. No blocked browser tests are counted as passing. Direct pytest
commands bypass this preflight. A passing smoke test is not a passing full suite.
After successful preflight, run `python -m pytest -ra python/tests/browser`.

Source guidance: https://playwright.dev/python/docs/browsers . Patch/ contains
release-specific measured validation results; these instructions are not results.


