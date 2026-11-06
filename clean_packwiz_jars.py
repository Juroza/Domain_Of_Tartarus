#!/usr/bin/env python3
"""Preview or delete raw JARs already named by packwiz metadata.

Usage (from the folder containing pack.toml):
    python3 ./clean_packwiz_jars.py
    python3 ./clean_packwiz_jars.py --delete
Requires Python 3.11+. Matches filenames, not file contents.
"""
import argparse
from pathlib import Path
import sys

try:
    import tomllib
except ImportError:
    sys.exit('Python 3.11 or newer is required. Try python3.11 instead of python3.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delete', action='store_true', help='Actually delete matching files; default is preview only.')
    parser.add_argument('--pack', type=Path, default=Path.cwd(), help='Pack folder containing pack.toml (default: current folder).')
    args = parser.parse_args()
    root = args.pack.expanduser().resolve()
    mods = root / 'mods'
    if not (root / 'pack.toml').is_file() or not mods.is_dir():
        parser.error('Run from the folder containing pack.toml and mods, or supply --pack PATH.')
    if mods.is_symlink():
        parser.error('The mods folder is a symbolic link; refusing to modify an external folder.')

    matches = set()
    # Parse every metadata file before making any deletions.
    for metadata in sorted(mods.rglob('*.pw.toml')):
        if metadata.is_symlink() or not metadata.resolve().is_relative_to(mods):
            continue
        try:
            with metadata.open('rb') as stream:
                data = tomllib.load(stream)
        except (OSError, tomllib.TOMLDecodeError) as error:
            parser.error(f'Cannot read {metadata.relative_to(root)}: {error}. No files deleted.')
        filename = data.get('filename')
        if not isinstance(filename, str) or not filename.lower().endswith('.jar'):
            continue
        if '/' in filename or '\\' in filename or '\x00' in filename:
            parser.error(f'Unsafe filename in {metadata.relative_to(root)}. No files deleted.')
        for name in (filename, filename + '.duplicate'):
            jar = metadata.parent / name
            if jar.is_file() and not jar.is_symlink():
                matches.add(jar)

    for jar in sorted(matches):
        if args.delete:
            try:
                jar.unlink()
            except OSError as error:
                sys.exit(f'Could not delete {jar}: {error}')
        print(f"{'Deleted' if args.delete else 'Would delete'}: {jar.relative_to(root)}")
    print(f"\n{len(matches)} matching file(s) {'deleted' if args.delete else 'found'}.")
    if args.delete:
        print('Now run: packwiz refresh')
    elif matches:
        print('Preview only. Run again with --delete to remove these files.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
