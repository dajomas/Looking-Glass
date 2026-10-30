## Bounded CI evidence reading copies (2026-10-30)

The collector now requires Python 3 and invokes `tools/chunk_ci_evidence.py`
before publishing. Original evidence is unchanged. A separate `reader-chunks/`
contains copies in parts of at most 4,000 bytes, an ordered paginated index,
per-source metadata and SHA-256 checksums for originals and parts. UTF-8 code
points are preserved; long lines and XML elements may span parts. Binary or
non-UTF-8 inputs use base64, decoded after concatenating their parts. Concatenate
parts without inserting newlines. Metadata and all reading-copy files are
bounded; oversized metadata fails explicitly. The exact connector threshold is
unknown, so this size is conservative rather than a guaranteed connector limit.
The helper verifies reconstruction against originals before exposing the reading
copy, and the collector verifies it again before staging. Files are read into
memory, so this is intended for CI evidence rather than arbitrarily large data.
Do not modify source evidence after chunking. Existing reading copies are not
overwritten. No existing published evidence is automatically rewritten.

For the already published run, execute:

```bash
python3 tools/chunk_ci_evidence.py ci-results-41011195909-attempt-1
python3 tools/chunk_ci_evidence.py --verify ci-results-41011195909-attempt-1
```

Review and publish only the generated reading copy on `features/perplexity`:

```bash
git add -- ci-results-41011195909-attempt-1/reader-chunks
git commit -m "Add readable chunks for CI run 41011195909 [skip ci]"
git push origin HEAD:refs/heads/features/perplexity
```

The existing run collector still refuses to reuse an output directory; use the
helper directly for already collected runs. No helper tests, shell syntax checks
or live GitHub integration tests were executed by the assistant for this change.
README.md was reviewed; its existing workflow overview remains accurate.

