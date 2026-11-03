"""Package local test logs compatibly and preserve the full diagnostic tree."""
import argparse
import base64
import gzip
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile


def package_results(source, prefix):
    source, prefix = Path(source), Path(prefix)
    if source.is_symlink() or not source.is_dir():
        raise ValueError("Results must be an existing non-symlink directory")
    source = source.resolve()
    outputs = (Path(str(prefix) + '.txt'), Path(str(prefix) + '.diagnostics.tar.gz'))
    for output in outputs:
        if output.resolve().is_relative_to(source):
            raise ValueError("Output files must be outside the results tree")
    entries = sorted(source.rglob('*'), key=lambda p: os.fsencode(p.relative_to(source)))
    if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in entries):
        raise ValueError("Symlinks and special files are not supported in diagnostic evidence")
    flat = sorted((p for p in entries if p.parent == source and p.is_file() and not p.name.startswith('.')),
                  key=lambda p: os.fsencode(p.name))
    prefix.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.lg-test-package-', dir=prefix.parent) as temporary:
        temporary = Path(temporary)
        compressed, legacy, bundle = (temporary / name for name in ('logs.gz', 'logs.txt', 'diagnostics.tar.gz'))
        with compressed.open('wb') as stream:
            for path in flat:
                with path.open('rb') as original, gzip.GzipFile(filename=path.name, mode='wb', fileobj=stream, mtime=0) as member:
                    shutil.copyfileobj(original, member)
            if not flat:
                with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0):
                    pass
        with compressed.open('rb') as original, legacy.open('wb') as encoded:
            base64.encode(original, encoded)
        with tarfile.open(bundle, mode='w:gz') as archive:
            archive.add(source, arcname='test-results', recursive=False)
            for path in entries:
                archive.add(path, arcname='test-results/' + path.relative_to(source).as_posix(), recursive=False)
        # Complete both products before publication; each replacement is atomic,
        # but the pair is not a filesystem transaction.
        os.replace(legacy, outputs[0])
        os.replace(bundle, outputs[1])
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('prefix', type=Path)
    args = parser.parse_args(argv)
    try:
        outputs = package_results(args.source, args.prefix)
    except (OSError, ValueError, tarfile.TarError) as exc:
        print(f'Test evidence packaging failed: {exc}', file=sys.stderr)
        return 1
    for output in outputs:
        print(f'Test evidence: {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
