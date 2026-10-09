#!/usr/bin/env python3
"""Separate 4-sigma SExtractor comparison; never modifies input ASDFs."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/roman-preview-matplotlib')
from pathlib import Path
import json, subprocess, tempfile, shutil, zipfile
import numpy as np
import roman_datamodels as rdm
from astropy.io import fits, ascii
from astropy.table import Table
from astropy.visualization import ImageNormalize,ZScaleInterval
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.collections import EllipseCollection
BASE=Path(__file__).resolve().parent
ROOT=Path('/path/to/Roman_I-Sim_reduction/F106')
for d in ['catalogs','previews','logs']: (BASE/d).mkdir(exist_ok=True)
reports=[]
for path in sorted((ROOT/'exposure_steps/11_flatfield').glob('r*_flatfield.asdf')):
    stem=path.stem.removesuffix('_flatfield'); receipt=BASE/'catalogs'/f'{stem}.json'
    if receipt.exists():
        reports.append(json.loads(receipt.read_text())); continue
    with rdm.open(str(path)) as model, tempfile.TemporaryDirectory(prefix='sex-',dir=BASE) as tmp:
        tmp=Path(tmp); data=np.array(model.data,dtype=np.float32); rms=np.array(model.err,dtype=np.float32)
        bad=~np.isfinite(data)|~np.isfinite(rms)|(rms<=0)|((model.dq&1)!=0)
        data[bad]=0; rms[bad]=1e30
        fits.writeto(tmp/'sci.fits',data); fits.writeto(tmp/'rms.fits',rms)
        catpath=BASE/'catalogs'/f'{stem}.sex.txt'
        cmd=['/opt/homebrew/bin/sex',str(tmp/'sci.fits'),'-c','sex.sex','-DETECT_THRESH','4','-ANALYSIS_THRESH','4','-WEIGHT_IMAGE',str(tmp/'rms.fits'),'-WEIGHT_THRESH','1e20','-CATALOG_NAME',str(catpath),'-MAG_ZEROPOINT','21','-PIXEL_SCALE','0.11','-CHECKIMAGE_TYPE','SEGMENTATION','-CHECKIMAGE_NAME',str(BASE/'catalogs'/f'{stem}_segmentation.fits')]
        with (BASE/'logs'/f'{stem}.log').open('w') as log: subprocess.run(cmd,cwd=BASE/'config',stdout=log,stderr=subprocess.STDOUT,check=True)
        tab=ascii.read(catpath,format='sextractor'); x=np.asarray(tab['XWIN_IMAGE'])-1; y=np.asarray(tab['YWIN_IMAGE'])-1
        ny,nx=data.shape
        sel=np.isfinite(x)&np.isfinite(y)&(x>=10)&(x<nx-10)&(y>=10)&(y<ny-10)&(tab['MAGERR_ISO']<=.2)&(tab['MAG_ISO']!=99)&(tab['ISOAREA_IMAGE']>=10)&(tab['FLUX_ISO']>0)&(tab['FLUXERR_ISO']>0)
        xi=np.clip(np.nan_to_num(x).astype(int),0,nx-1); yi=np.clip(np.nan_to_num(y).astype(int),0,ny-1); sel &= ~bad[yi,xi]
        candidate=Table({'id':tab['NUMBER'][sel],'xcentroid':x[sel],'ycentroid':y[sel],'flux':tab['FLUX_AUTO'][sel]})
        candidate.meta['coordinate_origin']=0
        candidate.write(BASE/'catalogs'/f'{stem}_phot.ecsv',format='ascii.ecsv',overwrite=True)
        norm=ImageNormalize(data,interval=ZScaleInterval())
        for kind,xx,yy in [('all',np.asarray(tab['X_IMAGE'])-1,np.asarray(tab['Y_IMAGE'])-1),('selected',x[sel],y[sel])]:
            fig,ax=plt.subplots(figsize=(8,8)); ax.imshow(data,origin='lower',cmap='gray_r',norm=norm)
            ax.add_collection(EllipseCollection(np.full(len(xx),24.),np.full(len(xx),24.),np.zeros(len(xx)),units='xy',offsets=np.column_stack((xx,yy)),offset_transform=ax.transData,facecolors='none',edgecolors='red',linewidths=.5))
            ax.set(xlim=(-.5,nx-.5),ylim=(-.5,ny-.5),title=f'{stem}\nSExtractor 4σ · {kind}: {len(xx)}')
            fig.savefig(BASE/'previews'/f'{stem}_{kind}.png',dpi=160,bbox_inches='tight'); plt.close(fig)
        old=json.loads((ROOT/'source_catalog'/f'{stem}_detection.json').read_text())
        r=dict(stem=stem,detected=len(tab),selected=int(sel.sum()),photutils_detected=old['detected'],photutils_selected=old['selected'],masked_pixels=int(bad.sum()))
        receipt.write_text(json.dumps(r,indent=2)); reports.append(r); print(json.dumps(r),flush=True)
    (BASE/'summary.json').write_text(json.dumps(reports,indent=2))
page=['<!doctype html><meta charset="utf-8"><title>SExtractor 4σ comparison</title><style>body{font:16px system-ui;margin:24px}img{width:100%}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:24px}</style><h1>SExtractor 4σ test</h1><p>Red circles: detections. Selected candidates use magnitude error ≤0.2, area ≥10 pixels and a 10-pixel border. No astrometric fitting.</p><main>']
for r in reports:
    s=r['stem']; page.append(f'<section><a href="{s}_all.png"><img loading="lazy" src="{s}_all.png"></a>{s}<p>SExtractor: {r["detected"]} detections; <a href="{s}_selected.png">{r["selected"]} selected</a>. Photutils: {r["photutils_detected"]} detections, {r["photutils_selected"]} selected.</p></section>')
(BASE/'previews/index.html').write_text('\n'.join(page+['</main>']))
(BASE/'summary.json').write_text(json.dumps(reports,indent=2))
with zipfile.ZipFile(BASE/'SExtractor_4sigma_previews.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in (BASE/'previews').iterdir():z.write(p,'previews/'+p.name)
print('COMPLETE',len(reports),flush=True)
