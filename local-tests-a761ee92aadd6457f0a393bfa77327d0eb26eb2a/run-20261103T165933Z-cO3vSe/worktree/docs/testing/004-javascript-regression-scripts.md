## JavaScript regression scripts

A focused UI check:

```sh
node python/tests/test_map_transitions.js
```

Run every top-level JavaScript regression script in PowerShell:

```powershell
Get-ChildItem python/tests/test_*.js | ForEach-Object {
    node $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "JavaScript regression failed: $($_.Name)" }
}
```

Or in a POSIX shell:

```sh
for test in python/tests/test_*.js; do
    node "$test" || exit 1
done
```

These scripts exercise helpers and DOM/transport mocks; they do not substitute for
real-browser rendering, pointer behavior, modal focus or network timing tests.

