#!/usr/bin/env python3
"""Download public Roman I-Sim F106 exposures; Python 3.9+, no dependencies.

Examples:
  python3 download_roman_isim.py --dry-run
  python3 download_roman_isim.py
  python3 download_roman_isim.py --level both
"""
import argparse
import os
from pathlib import Path
import re
import time
from urllib.parse import urlencode, quote
from urllib.request import urlopen
import xml.etree.ElementTree as ET

BUCKET = 'https://stpubdata.s3.amazonaws.com'
PREFIX = 'roman/nexus/soc_simulations/tutorial_data/roman-2026.2/'
ROOT = 'r0003201001001001004'
DEFAULT_DEST = '/path/to/Roman_I-Sim_reduction'
NS = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}


def list_images(levels):
    pattern = re.compile(rf'{ROOT}_(000[1-4])_wfi(0[1-9]|1[0-8])_f106_(uncal|cal)\.asdf')
    query = {'list-type': '2', 'prefix': PREFIX + ROOT + '_'}
    found = []
    while True:
        with urlopen(BUCKET + '/?' + urlencode(query), timeout=60) as response:
            tree = ET.parse(response).getroot()
        for item in tree.findall('s:Contents', NS):
            key = item.findtext('s:Key', namespaces=NS)
            match = pattern.fullmatch(key.rsplit('/', 1)[-1])
            if match and match.group(3) in levels:
                found.append((key, int(item.findtext('s:Size', namespaces=NS)), match.group(3)))
        token = tree.findtext('s:NextContinuationToken', namespaces=NS)
        if not token:
            break
        query['continuation-token'] = token
    for level in levels:
        count = sum(kind == level for _, _, kind in found)
        if count != 72:
            raise RuntimeError(f'Expected 72 {level} files (4 exposures x 18 detectors), found {count}; stopping.')
    return sorted(found)


def download(key, size, target):
    if target.exists():
        if target.stat().st_size == size:
            print('  Skip existing complete file', flush=True)
            return
        raise RuntimeError(f'Existing file has unexpected size; move it aside before retrying: {target}')
    partial = target.with_suffix(target.suffix + '.part')
    for attempt in range(1, 4):
        try:
            with urlopen(BUCKET + '/' + quote(key, safe='/'), timeout=120) as source, partial.open('wb') as out:
                while True:
                    chunk = source.read(8 * 1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            if partial.stat().st_size != size:
                raise IOError(f'Size mismatch: expected {size}, got {partial.stat().st_size}')
            os.replace(partial, target)
            return
        except Exception as exc:
            if attempt == 3:
                raise
            print(f'  Attempt {attempt} failed: {exc}; retrying', flush=True)
            time.sleep(2 * attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--level', choices=['uncal', 'cal', 'both'], default='uncal')
    parser.add_argument('--dest', type=Path, default=Path(DEFAULT_DEST))
    parser.add_argument('--dry-run', action='store_true', help='List remote files and sizes without writing anything')
    args = parser.parse_args()
    levels = ['uncal', 'cal'] if args.level == 'both' else [args.level]
    files = list_images(levels)
    total = sum(size for _, size, _ in files)
    print(f'{len(files)} files, {total / 1e9:.2f} GB ({total / 2**30:.2f} GiB). Destination: {args.dest}', flush=True)
    if not args.dry_run:
        # Prevent accidentally creating a missing external volume on the system disk.
        if str(args.dest).startswith('/Volumes/'):
            volume = Path('/Volumes') / args.dest.parts[2]
            if not volume.is_mount():
                raise RuntimeError(f'External volume is not mounted: {volume}')
        for level in levels:
            (args.dest / level).mkdir(parents=True, exist_ok=True)
    for index, (key, size, level) in enumerate(files, 1):
        target = args.dest / level / key.rsplit('/', 1)[-1]
        print(f'[{index}/{len(files)}] {target.name} ({size / 1e6:.1f} MB)', flush=True)
        if not args.dry_run:
            download(key, size, target)
    print('Dry run complete; no files written.' if args.dry_run else 'Download complete.')


if __name__ == '__main__':
    main()
