#!/usr/bin/env python3
"""Export Roman ASDF science arrays to individual FITS files with validated celestial WCS."""
from pathlib import Path
import argparse,json,tempfile
import numpy as np
import roman_datamodels as rdm
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('inputs',nargs='+',type=Path);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--max-wcs-error',type=float,default=.01,help='Maximum tested WCS error in pixels')
 a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 for path in a.inputs:
  if path.name.startswith('._'):continue
  receipt=a.output_dir/(path.stem+'_fits_export.json')
  if receipt.exists():raise FileExistsError(f'Export exists: {receipt}')
  with rdm.open(str(path)) as m:
   assert m.data.ndim==2,'Export a selected ramp plane separately; this tool expects a2D image'
   ny,nx=m.data.shape
   h=m.meta.wcs.to_fits_sip(max_pix_error=a.max_wcs_error/10,max_inv_pix_error=a.max_wcs_error/10,npoints=32)
   fw=WCS(h).celestial
   # Independent grid differs from fit sampling; checks actual sky mapping and inverse.
   x,y=np.meshgrid(np.linspace(0,nx-1,43),np.linspace(0,ny-1,41));x=x.ravel();y=y.ravel()
   ra,dec=m.meta.wcs(x,y,with_bounding_box=False);xf,yf=fw.all_world2pix(ra,dec,0)
   err=float(np.max(np.hypot(xf-x,yf-y)));assert np.isfinite(err) and err<a.max_wcs_error,err
   flux=m.meta.cal_step.get('flux')=='COMPLETE' or m.meta.cal_step.get('resample')=='COMPLETE'
   units='MJy/sr' if flux else 'DN/s'
   h['FILTER']=str(m.meta.instrument.optical_element);h['ORIGFILE']=path.name;h['WCSERR']=err;h['HISTORY']='FITS celestial WCS fitted to Roman GWCS; original ASDF retained.'
   h['HISTORY']='No pixel shift applied. FITS CRPIX convention handled by GWCS exporter.'
   h['HISTORY']='Nonfinite pixels preserved. Background estimation uncertainty not propagated.'
   exported=[]
   for key,suffix in [('data','sci'),('err','err'),('weight','wht'),('var_poisson','var_poisson'),('var_rnoise','var_rnoise'),('var_flat','var_flat'),('dq','dq'),('context','context')]:
    if not hasattr(m,key):continue
    dest=a.output_dir/(path.stem+'_'+suffix+'.fits')
    if dest.exists():raise FileExistsError(dest)
    arr=np.asarray(m[key]);header=h.copy();header['EXTNAME']=key.upper()
    if key in ['data','err']:header['BUNIT']=units
    elif key.startswith('var_'):header['BUNIT']='('+units+')^2'
    elif key in ['dq','context']:header['BUNIT']='1'
    else:header['HISTORY']='Pipeline drizzle weight retained without an assumed physical unit.'
    if key=='var_flat' and np.all(~np.isfinite(arr)):header['HISTORY']='All NaN: this product has no available flat variance contribution.'
    with tempfile.TemporaryDirectory(prefix='.fits-export-',dir=a.output_dir) as tmp:
     temp=Path(tmp)/dest.name;fits.PrimaryHDU(arr,header).writeto(temp,checksum=True)
     with fits.open(temp,memmap=False,checksum=True) as hd:
      assert hd[0].verify_checksum()==1 and hd[0].verify_datasum()==1
      assert hd[0].data.shape==arr.shape
      for yy in range(0,ny,128):
       sl=(slice(None),slice(yy,yy+128),slice(None)) if arr.ndim==3 else (slice(yy,yy+128),slice(None))
       assert np.array_equal(hd[0].data[sl],arr[sl],equal_nan=True)
     temp.rename(dest)
    exported.append(dict(array=key,path=str(dest),shape=list(arr.shape),bytes=dest.stat().st_size));print('EXPORTED',dest,flush=True)
   receipt.write_text(json.dumps(dict(input=str(path),units=units,wcs_max_error_pixels=err,validation='Independent43x41 WCS grid; FITS checksums; exact pixel values including NaNs',files=exported),indent=2))
if __name__=='__main__':main()
