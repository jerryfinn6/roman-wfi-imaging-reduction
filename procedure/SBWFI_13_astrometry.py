#!/usr/bin/env python3
"""Individually align Roman frames to simulation truth using SExtractor centroids."""
from pathlib import Path
import argparse,json,copy,os
import numpy as np
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
import roman_datamodels as rdm
from romancal.tweakreg import TweakRegStep
from romancal.datamodels import ModelLibrary

OPTIONS=dict(enforce_user_order=True,expand_refcat=False,minobj=10,use2dhist=False,fitgeometry='shift',separation=.2,tolerance=.1,searchrad=3.,nclip=1,sigma=.7,abs_minobj=10,abs_searchrad=240.,abs_nclip=3,abs_sigma=3.,abs_separation=1.,abs_tolerance=.5,abs_use2dhist=True,abs_fitgeometry='general',update_source_catalog_coordinates=False)
def stats(sky,ref):
    dx,dy=ref.spherical_offsets_to(sky)
    sep=sky.separation(ref).mas
    return dict(n=len(sep),median_mas=float(np.median(sep)),p90_mas=float(np.percentile(sep,90)),rms_mas=float(np.sqrt(np.mean(sep**2))),median_dra_mas=float(np.median(dx.mas)),median_ddec_mas=float(np.median(dy.mas)))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    base=Path(__file__).resolve().parent.parent
    if not (base/'full_catalog.ecsv').exists():base=Path('/path/to/work/outputs')
    p.add_argument('--root',type=Path,default=Path('/path/to/Roman_I-Sim_reduction'))
    p.add_argument('--catalog-dir',type=Path,default=base/'roman_sextractor_4sigma_test/catalogs')
    p.add_argument('--truth',type=Path,default=base/'full_catalog.ecsv')
    p.add_argument('--output-dir',type=Path,default=base/'roman_tweakreg_test')
    p.add_argument('--all',action='store_true',help='Process all72; default tests first exposure WFI01/07/14')
    a=p.parse_args();out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    truth=Table.read(a.truth);truth=truth[(truth['type']=='PSF')&np.isfinite(truth['ra'])&np.isfinite(truth['dec'])]
    coords=SkyCoord(truth['ra'],truth['dec'],unit='deg'); reports=[]
    files=sorted((a.root/'F106/exposure_steps/11_flatfield').glob('r*_flatfield.asdf'))
    if not a.all:files=[f for f in files if '_0001_' in f.name and any('_'+d+'_' in f.name for d in ['wfi01','wfi07','wfi14'])]
    for path in files:
        stem=path.stem.removesuffix('_flatfield'); receipt=out/f'{stem}_validation.json'; target=out/f'{stem}_tweakreg.asdf'
        if receipt.exists() and target.exists():reports.append(json.loads(receipt.read_text()));continue
        if target.exists():raise RuntimeError(f'Unvalidated output exists: {target}')
        tab=Table.read(a.catalog_dir/f'{stem}_phot.ecsv');assert tab.meta['coordinate_origin']==0
        cat=Table({'id':tab['id'],'x':tab['xcentroid'],'y':tab['ycentroid'],'flux':tab['flux']});catpath=out/f'{stem}_xy.ecsv';cat.write(catpath,overwrite=True)
        with rdm.open(str(path)) as model:
            original_wcs=copy.deepcopy(model.meta.wcs)
            center=SkyCoord(*original_wcs(2043.5,2043.5),unit='deg');near=coords.separation(center)<.20*u.deg
            ref=Table({'RA':truth['ra'][near],'DEC':truth['dec'][near]});refpath=out/f'{stem}_reference.ecsv';ref.write(refpath,overwrite=True)
            refsky=SkyCoord(ref['RA'],ref['DEC'],unit='deg')
            before=SkyCoord(*original_wcs(cat['x'],cat['y']),unit='deg'); idx,sep,_=before.match_to_catalog_sky(refsky)
            model.meta.source_catalog={'tweakreg_catalog_name':str(catpath)}
            library=TweakRegStep.call(ModelLibrary([model]),abs_refcat=str(refpath),save_results=False,**OPTIONS)
            with library:
                aligned=library.borrow(0)
                if aligned.meta.cal_step.tweakreg!='COMPLETE':raise RuntimeError(str(aligned.meta.wcs_fit_results))
                after=SkyCoord(*aligned.meta.wcs(cat['x'],cat['y']),unit='deg')
                # Post-fit unique pairs, reused unchanged for before/after residuals.
                idx,sep,_=after.match_to_catalog_sky(refsky)
                order=np.argsort(sep.arcsec);used=set();keep=[]
                for j in order:
                    if sep[j].arcsec<.1 and int(idx[j]) not in used:keep.append(int(j));used.add(int(idx[j]))
                keep=np.array(keep,dtype=int);assert len(keep)>=10
                metrics=dict(stem=stem,input=str(path),output=str(target),reference=str(refpath),reference_stars=len(ref),input_sources=len(cat),parameters=OPTIONS,before=stats(before[keep],refsky[idx[keep]]),after=stats(after[keep],refsky[idx[keep]]),fit_info=dict(aligned.meta.wcs_fit_results),romancal='1.1.0',crds_context=os.environ.get('CRDS_CONTEXT'))
                residual=Table({'id':cat['id'][keep],'reference_row':idx[keep],'before_mas':before[keep].separation(refsky[idx[keep]]).mas,'after_mas':after[keep].separation(refsky[idx[keep]]).mas})
                residual.write(out/f'{stem}_residuals.ecsv',overwrite=True)
                aligned.meta.filename=target.name;aligned.save(str(target));library.shelve(aligned,0)
        with rdm.open(str(path)) as orig,rdm.open(str(target)) as saved:
            for name in ['data','dq','err','var_poisson','var_rnoise','var_flat']:
                if hasattr(orig,name):assert np.array_equal(getattr(orig,name),getattr(saved,name),equal_nan=True),name
            assert saved.meta.cal_step.tweakreg=='COMPLETE'
            px=np.array([10.,2043.5,4077.]);py=px[::-1];ra,dec=saved.meta.wcs(px,py);xx,yy=saved.meta.wcs.invert(ra,dec)
            metrics['wcs_roundtrip_max_pixel']=float(np.max(np.hypot(xx-px,yy-py)));assert metrics['wcs_roundtrip_max_pixel']<.01
            metrics['science_arrays_unchanged']=True
        receipt.write_text(json.dumps(metrics,indent=2,default=lambda v:float(v) if isinstance(v,np.floating) else (list(v) if hasattr(v,'__iter__') else v.item())))
        reports.append(metrics);print(json.dumps(metrics,default=lambda v:float(v) if isinstance(v,np.floating) else (list(v) if hasattr(v,'__iter__') else v.item())),flush=True)
        (out/'summary.json').write_text(json.dumps(reports,indent=2,default=lambda v:float(v) if isinstance(v,np.floating) else (list(v) if hasattr(v,'__iter__') else v.item())))
    print('COMPLETE',len(reports),flush=True)
if __name__=='__main__':main()
