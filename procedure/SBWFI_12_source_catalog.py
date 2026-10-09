#!/usr/bin/env python3
"""Run Roman source catalogs and produce zero-based astrometry candidates/overlays."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/roman-preview-matplotlib')
from pathlib import Path
import argparse,json,sys,html
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.collections import EllipseCollection
from astropy.visualization import ImageNormalize,ZScaleInterval
from astropy.table import Table
import roman_datamodels as rdm
from romancal.source_catalog import SourceCatalogStep

OPTIONS=dict(snr_threshold=4.0,npixels=5,kernel_fwhm=2.0,bkg_boxsize=128,deblend=True,fit_psf=False)

def run(path,out,previews):
    out.mkdir(parents=True,exist_ok=True);previews.mkdir(parents=True,exist_ok=True)
    stem=path.stem.removesuffix('_flatfield')
    done=out/(stem+'_detection.json')
    if done.exists() and json.loads(done.read_text()).get('selection_version') == 2:return json.loads(done.read_text())
    with rdm.open(str(path)) as model:
        cat,seg=SourceCatalogStep.call(model,save_results=False,**OPTIONS)
        table=cat.source_catalog
        cat.save(str(out/(stem+'_cat.parquet')))
        seg.save(str(out/(stem+'_segm.asdf')))
        table.write(out/(stem+'_all.ecsv'),format='ascii.ecsv',overwrite=True)
        def arr(k):return np.asarray(table[k],dtype=float)
        x,y=arr('x_centroid_win'),arr('y_centroid_win')
        flux,err=arr('segment_flux'),arr('segment_flux_err')
        with np.errstate(divide='ignore',invalid='ignore'):
            magerr=2.5/np.log(10)*err/flux
        ny,nx=model.data.shape
        # Pipeline segment_area is sky area; count segmentation pixels for ISOAREA equivalence.
        counts=np.bincount(np.asarray(seg.data).ravel().astype(np.int64))
        area_pixels=counts[np.asarray(table['label'],dtype=int)]
        selected=np.isfinite(x)&np.isfinite(y)&(x>=10)&(x<nx-10)&(y>=10)&(y<ny-10)&(flux>0)&(err>0)&np.isfinite(magerr)&(magerr<=.2)&(area_pixels>=10)
        # Reject candidates centered on pixels excluded by the source step.
        xi=np.clip(np.nan_to_num(x,nan=0).astype(int),0,nx-1)
        yi=np.clip(np.nan_to_num(y,nan=0).astype(int),0,ny-1)
        selected &= ((model.dq[yi,xi]&1)==0)&np.isfinite(model.data[yi,xi])&np.isfinite(model.err[yi,xi])&(model.err[yi,xi]>0)
        candidates=Table({'id':table['label'][selected],'xcentroid':x[selected],'ycentroid':y[selected],
                          'flux':arr('kron_flux')[selected],'segment_flux':flux[selected],
                          'segment_flux_err':err[selected],'magerr_segment':magerr[selected],
                          'segment_area_pixels':area_pixels[selected]})
        candidates.meta['coordinate_origin']=0
        candidates.meta['selection']='windowed centroids; 10-pixel border on all sides; segment area >=10; positive segment flux/error; 1.085736*err/flux <=0.2'
        candidates.write(out/(stem+'_phot.ecsv'),format='ascii.ecsv',overwrite=True)
        data=np.array(model.data,copy=True);data[~np.isfinite(data)]=0
        norm=ImageNormalize(data,interval=ZScaleInterval())
        for kind,xx,yy in [('all',arr('x_centroid'),arr('y_centroid')),('selected',x[selected],y[selected])]:
            good=np.isfinite(xx)&np.isfinite(yy);xx=xx[good];yy=yy[good]
            fig,ax=plt.subplots(figsize=(8,8));ax.imshow(data,cmap='gray_r',origin='lower',norm=norm)
            marks=EllipseCollection(np.full(len(xx),24.),np.full(len(xx),24.),np.zeros(len(xx)),units='xy',offsets=np.column_stack((xx,yy)),offset_transform=ax.transData,facecolors='none',edgecolors='red',linewidths=.5)
            ax.add_collection(marks);ax.set_xlim(-.5,nx-.5);ax.set_ylim(-.5,ny-.5)
            ax.set_title(f"F106 · {stem.split('_')[1]} · {model.meta.instrument.detector}\n{kind}: {len(xx)} sources; 4σ detection",fontsize=11)
            fig.savefig(previews/(stem+f'_{kind}.png'),dpi=160,bbox_inches='tight');plt.close(fig)
        info={'input':str(path),'stem':stem,'detected':len(table),'selected':int(selected.sum()),'parameters':OPTIONS,'coordinate_origin':0,'selection_version':2}
        done.write_text(json.dumps(info,indent=2));cat.close();seg.close()
        return info

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('filter',nargs='?',default='F106')
    p.add_argument('--root',type=Path,default=Path('/path/to/Roman_I-Sim_reduction'))
    p.add_argument('--limit',type=int);p.add_argument('--preview-dir',type=Path)
    a=p.parse_args();files=sorted((a.root/a.filter/'exposure_steps/11_flatfield').glob('r*_flatfield.asdf'))
    if a.limit:files=files[:a.limit]
    out=a.root/a.filter/'source_catalog';previews=a.preview_dir or a.root/a.filter/'source_catalog_imshow'
    reports=[]
    for f in files:
        info=run(f,out,previews);reports.append(info);print(json.dumps(info),flush=True)
        (out/'summary.json').write_text(json.dumps(reports,indent=2))
    page=['<!doctype html><meta charset="utf-8"><title>Roman source detections</title><style>body{font:16px system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px}img{width:100%}figure{margin:0}</style><h1>Roman source detections</h1><p>Red circles: all detections. Links show the brighter alignment-candidate subset. Coordinates are zero-based; no astrometric fit has been applied.</p><main>']
    for r in reports:
        s=r['stem'];page.append(f'<figure><a href="{s}_all.png"><img loading="lazy" src="{s}_all.png"></a><figcaption>{html.escape(s)}<br>{r["detected"]} detections · <a href="{s}_selected.png">{r["selected"]} alignment candidates</a></figcaption></figure>')
    (previews/'index.html').write_text('\n'.join(page+['</main>']))
if __name__=='__main__':main()
