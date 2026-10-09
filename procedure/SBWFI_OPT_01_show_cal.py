#!/usr/bin/env python3
"""Roman version of SBNRC_OPT_01_show_cal: gray_r, ZScale, origin lower, 160 dpi."""
import argparse
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/roman-preview-matplotlib')
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from astropy.visualization import ImageNormalize, ZScaleInterval
import roman_datamodels as rdm
import numpy as np
import html

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('filter',nargs='?',default='F106')
p.add_argument('--root',type=Path,default=Path.cwd())
p.add_argument('--input-dir',type=Path)
p.add_argument('--output-dir',type=Path)
a=p.parse_args()
source=a.input_dir or a.root/a.filter/'exposure_steps/11_flatfield'
out=a.output_dir or a.root/a.filter/'stage2_cal_imshow'
out.mkdir(parents=True,exist_ok=True)
files=sorted(f for f in source.glob('*_flatfield.asdf') if not f.name.startswith('.'))
if not files: raise SystemExit(f'No flat-fielded images found in {source}')
entries=[]
for i,f in enumerate(files,1):
    with rdm.open(str(f)) as model:
        data=np.array(model.data,copy=True)
        detector=str(model.meta.instrument.detector)
    # Display-only replacement; ASDF science arrays and DQ are unchanged.
    data[~np.isfinite(data)]=0
    norm=ImageNormalize(data,interval=ZScaleInterval())
    fig,ax=plt.subplots(figsize=(7,6))
    ax.imshow(data,norm=norm,cmap='gray_r',origin='lower')
    exposure=f.name.split('_')[1]
    label=f'{a.filter} · exposure {exposure} · {detector}'
    ax.set_title(label)
    target=out/(f.stem.removesuffix('_flatfield')+'_imshow.png')
    fig.savefig(target,dpi=160,bbox_inches='tight');plt.close(fig)
    entries.append((label,target.name))
    print(f'[{i}/{len(files)}] {target.name}',flush=True)
# A local browsing index, requiring no server or network.
parts=['<!doctype html><meta charset="utf-8"><title>Roman WFI previews</title>',
 '<style>body{font:16px system-ui;margin:24px;background:#eee}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}figure{margin:0;background:white;padding:8px}img{width:100%}a{color:#164b83}</style>',
 f'<h1>Roman {html.escape(a.filter)}: {len(entries)} calibrated-frame previews</h1>',
 '<p>Individual ZScale stretches; grayscale reversed, origin lower. Click an image to open full size. Non-finite pixels display as zero. No DQ masking or science-data changes.</p><main>']
for label,name in entries:
 parts.append(f'<figure><a href="{html.escape(name)}"><img loading="lazy" src="{html.escape(name)}" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>')
parts.append('</main>')
(out/'index.html').write_text('\n'.join(parts))
