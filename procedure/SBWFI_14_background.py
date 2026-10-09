#!/usr/bin/env python3
"""Independent detector-frame Background2D subtraction following SBNRC_03."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/roman-preview-matplotlib')
from pathlib import Path
import argparse,json
import numpy as np
import roman_datamodels as rdm
from astropy.stats import SigmaClip
from astropy.io import fits
from astropy.visualization import ImageNormalize,ZScaleInterval
from photutils.background import Background2D,MedianBackground
from photutils.segmentation import detect_threshold,detect_sources
from photutils.utils import circular_footprint
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
OPTIONS=dict(source_sigma=3,min_area=10,dilate_radius=10,clip_sigma=3,maxiters=10,box_size=128,filter_size=5,exclude_percentile=80)
def main():
 p=argparse.ArgumentParser(description=__doc__);base=Path('/path/to/work/outputs')
 p.add_argument('--input-dir',type=Path,default=base/'roman_tweakreg_test');p.add_argument('--output-dir',type=Path,default=base/'roman_background');p.add_argument('--limit',type=int)
 a=p.parse_args();out=a.output_dir;out.mkdir(parents=True,exist_ok=True);reports=[]
 files=sorted(a.input_dir.glob('r*_tweakreg.asdf'))
 if a.limit:files=files[:a.limit]
 for path in files:
  stem=path.stem.removesuffix('_tweakreg');receipt=out/f'{stem}_background.json';target=out/f'{stem}_bkgsub.asdf'
  if receipt.exists() and target.exists():reports.append(json.loads(receipt.read_text()));continue
  if target.exists():raise RuntimeError(f'Unvalidated output: {target}')
  with rdm.open(str(path)) as m:
   units='MJy/sr' if m.meta.cal_step.flux=='COMPLETE' else 'DN/s'
   data=np.array(m.data,copy=True);invalid=~np.isfinite(data)|~np.isfinite(m.err)|(m.err<=0)|((m.dq&1)!=0)|(data==0)
   estimate=data.copy();estimate[invalid]=np.nan;clip=SigmaClip(sigma=3,maxiters=10)
   threshold=detect_threshold(estimate,3,mask=invalid,sigma_clip=clip)
   seg=detect_sources(estimate,threshold,10,mask=invalid)
   sources=np.zeros(data.shape,dtype=bool) if seg is None else seg.make_source_mask(footprint=circular_footprint(radius=10))
   mask=invalid|sources
   b=Background2D(estimate,(128,128),filter_size=(5,5),mask=mask,sigma_clip=clip,bkg_estimator=MedianBackground(),exclude_percentile=80)
   background=np.asarray(b.background,dtype=data.dtype);assert np.all(np.isfinite(background))
   sub=data-background;valid=~mask
   header=fits.Header();header['BUNIT']=units;header['COMMENT']='Pixel-aligned background; use companion ASDF for GWCS.'
   fits.HDUList([fits.PrimaryHDU(background,header=header),fits.ImageHDU(np.asarray(b.background_rms,dtype=np.float32),name='BKG_RMS'),fits.ImageHDU(mask.astype(np.uint8),name='MASK')]).writeto(out/f'{stem}_background.fits',overwrite=True)
   m.data=sub;m.meta.filename=target.name;m.save(str(target))
   info=dict(units=units,stem=stem,input=str(path),output=str(target),parameters=OPTIONS,masked_fraction=float(mask.mean()),background_median=float(np.median(background)),unmasked_median_before=float(np.median(data[valid])),unmasked_median_after=float(np.median(sub[valid])),model_range=[float(background.min()),float(background.max())])
   fig,axes=plt.subplots(1,3,figsize=(16,5));norm=ImageNormalize(data[::4,::4],interval=ZScaleInterval())
   for ax,img,title in zip(axes,[data,background,sub],['Aligned input','2D background','Background subtracted']):
    ax.imshow(img[::4,::4],origin='lower',cmap='gray_r',norm=norm if title=='Aligned input' else ImageNormalize(img[::4,::4],interval=ZScaleInterval()));ax.set_title(title+' (own stretch)')
   fig.suptitle(stem);fig.tight_layout();fig.savefig(out/f'{stem}_preview.png',dpi=120);plt.close(fig)
  with rdm.open(str(path)) as original,rdm.open(str(target)) as saved:
   assert np.allclose(saved.data,sub,equal_nan=True)
   for key in ['dq','err','var_poisson','var_rnoise','var_flat']:
    if hasattr(original,key):assert np.array_equal(getattr(original,key),getattr(saved,key),equal_nan=True)
   x=np.array([10.,2043.,4077.]);assert np.allclose(original.meta.wcs(x,x),saved.meta.wcs(x,x))
  info['validation']='subtraction, unchanged uncertainty/DQ and WCS verified';receipt.write_text(json.dumps(info,indent=2));reports.append(info);print(json.dumps(info),flush=True)
 (out/'summary.json').write_text(json.dumps(reports,indent=2))
 (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><h1>Per-detector 2D background subtraction</h1><p>Each panel uses its own stretch.</p>'+''.join(f'<p>{r["stem"]}</p><img style="width:100%;max-width:1500px" loading="lazy" src="{r["stem"]}_preview.png">' for r in reports))
 print('COMPLETE',len(reports),flush=True)
if __name__=='__main__':main()
