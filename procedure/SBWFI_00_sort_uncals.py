#!/usr/bin/env python3
"""Sort Roman L1 ASDF files by metadata optical_element into FILTER/stage1.
Default: dry run. --apply moves files. Partial downloads are never selected.
Run from the reduction directory or pass --root. Leaves uncal/ for later downloads.
"""
import argparse
from pathlib import Path
import json
import re
from datetime import datetime, timezone
import asdf

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=Path, default=Path.cwd())
p.add_argument('--input-dir', default='uncal')
p.add_argument('--apply', action='store_true')
a = p.parse_args()
root = a.root.resolve()
plan = []
# Validate all inputs before moving any; ASDF arrays stay lazy.
for src in sorted((root / a.input_dir).glob('*_uncal.asdf')):
    if src.name.startswith('.'):
        continue  # macOS AppleDouble metadata is not an ASDF dataset
    with asdf.open(src) as af:
        m = af['roman']['meta']
        if m['instrument']['name'] != 'WFI' or m['exposure']['type'] != 'WFI_IMAGE':
            raise ValueError(f'Not WFI imaging: {src}')
        filt = str(m['instrument']['optical_element']).upper()
        if not re.fullmatch(r'F\d{3}', filt):
            raise ValueError(f'Unexpected imaging filter {filt}: {src}')
        shape = tuple(af['roman']['data'].shape)
        if len(shape) != 3:
            raise ValueError(f'Expected L1 cube: {src}: {shape}')
        detector = str(m['instrument']['detector'])
    dest = root / filt / 'stage1' / src.name
    if dest.exists():
        raise FileExistsError(f'Will not overwrite {dest}; inspect duplicate input {src}')
    plan.append(dict(source=str(src), destination=str(dest), filter=filt,
                     detector=detector, bytes=src.stat().st_size, shape=shape))
for row in plan:
    print(f"{row['detector']} {row['filter']}: {Path(row['destination']).relative_to(root)}")
if a.apply and plan:
    logdir = root / 'logs'; logdir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    manifest = logdir / f'sort_uncals_{stamp}.json'
    manifest.write_text(json.dumps({'status':'planned','files':plan}, indent=2))
    for row in plan:
        dest = Path(row['destination']); dest.parent.mkdir(parents=True, exist_ok=True)
        Path(row['source']).rename(dest)
    manifest.write_text(json.dumps({'status':'completed','files':plan}, indent=2))
print(f"{'Moved' if a.apply else 'Would move'} {len(plan)} files.")
