from pathlib import Path
import os
os.environ['MPLCONFIGDIR']='/tmp/roman-preview-matplotlib'
import numpy as np,json
import roman_datamodels as rdm
from astropy.io import fits
from astropy.stats import SigmaClip
from astropy.visualization import simple_norm
from photutils.background import Background2D,MedianBackground
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
base=Path('/path/to/work/outputs');out=base/'roman_wfi14_background_review';s='r0003201001001001004_0001_wfi14_f106'
with rdm.open(str(base/'roman_tweakreg_test'/f'{s}_tweakreg.asdf')) as m:
 data=np.array(m.data);bad=~np.isfinite(data)|~np.isfinite(m.err)|(m.err<=0)|((m.dq&1)!=0)|(data==0)
with fits.open(base/'roman_background'/f'{s}_background.fits') as f:old=f[0].data.copy();mask=f['MASK'].data.astype(bool)
# Locate the galaxy peak in the feature's known small region.
cut=np.nan_to_num(data[2000:2300,650:900],nan=0);peak=np.unravel_index(np.argmax(gaussian_filter(cut,20)),cut.shape);cy,cx=peak[0]+2000,peak[1]+650
Y,X=np.ogrid[:data.shape[0],:data.shape[1]];r=np.hypot(X-cx,Y-cy);large=mask|(r<300)
est=data.copy();est[bad]=np.nan
b=Background2D(est,(128,128),filter_size=(5,5),mask=large,sigma_clip=SigmaClip(sigma=3,maxiters=10),bkg_estimator=MedianBackground(),exclude_percentile=80)
new=b.background;delta=old-new
sl=(slice(cy-450,cy+451),slice(cx-450,cx+451));extent=(-450,450,-450,450)
fig,axes=plt.subplots(2,3,figsize=(15,10));orig=data[sl]-np.median(new[sl]);norm=simple_norm(orig,stretch='asinh',vmin=-.015,vmax=.12)
items=[(orig,'Input minus local constant sky',norm),(mask[sl],'Current estimation mask (white = masked)',None),(delta[sl],'Current − enlarged-mask background [DN/s]',None),(data[sl]-old[sl],'Current subtraction',norm),(data[sl]-new[sl],'Test: mask galaxy to radius 300 px',norm),(large[sl],'Test estimation mask',None)]
for ax,(img,title,n) in zip(axes.flat,items):
 kw=dict(origin='lower',extent=extent,cmap='gray_r' if n else 'gray')
 if n:kw['norm']=n
 if title.startswith('Current −'):kw.update(cmap='coolwarm',vmin=-.025,vmax=.025)
 im=ax.imshow(img,**kw);ax.set_title(title);ax.set_xlabel('x − galaxy center [pixels]');ax.set_ylabel('y − galaxy center [pixels]')
 if title.startswith('Current −'):fig.colorbar(im,ax=ax,fraction=.046)
fig.suptitle(f'WFI14 exposure 0001 — galaxy at zero-based ({cx}, {cy})\nExpanded mask is a diagnostic, not a validated replacement background');fig.tight_layout();fig.savefig(out/'galaxy_comparison.png',dpi=150)
fig,ax=plt.subplots(figsize=(8,5));radii=np.arange(10,401,10);oldprof=[];newprof=[];diffprof=[]
for rr in radii:
 sel=(r>=rr-10)&(r<rr)&~bad
 oldprof.append(float(np.median((data-old)[sel])));newprof.append(float(np.median((data-new)[sel])));diffprof.append(float(np.median(delta[sel])))
ax.plot(radii-5,oldprof,label='Current subtraction');ax.plot(radii-5,newprof,label='300-pixel mask test');ax.plot(radii-5,diffprof,label='Additional background removed by current model',ls='--');ax.set(xlabel='Radius from galaxy center [pixels]',ylabel='Annular median [DN/s]',ylim=(-.005,.025),title='Galaxy outskirts: sensitivity to background mask');ax.axhline(0,color='gray',lw=.7);ax.legend();fig.tight_layout();fig.savefig(out/'radial_profile.png',dpi=150)
info=dict(center_zero_based=[int(cx),int(cy)],test_mask_radius_pixels=300,annular_radius_pixels=(radii-5).tolist(),current_profile=oldprof,expanded_mask_profile=newprof,extra_subtraction_profile=diffprof,delta_minmax=[float(delta[sl].min()),float(delta[sl].max())]);(out/'review.json').write_text(json.dumps(info,indent=2));print(json.dumps(info))
