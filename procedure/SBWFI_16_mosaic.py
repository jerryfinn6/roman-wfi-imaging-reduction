#!/usr/bin/env python3
"""Prepare Roman mosaic association/WCS; add --run to execute outlier detection + drizzle."""
import argparse,json,os,tempfile
os.environ.setdefault("MPLCONFIGDIR","/tmp/roman-preview-matplotlib")
from pathlib import Path
from importlib.metadata import version
import numpy as np
import asdf
import roman_datamodels as rdm
from astropy.coordinates import SkyCoord
from romancal.associations.asn_from_list import asn_from_list
from romancal.datamodels import ModelLibrary
from romancal.resample.resample import make_output_wcs
from romancal.pipeline import MosaicPipeline

class ExposureGroupedLibrary(ModelLibrary):
 """Propagate explicit association exposure groups into borrowed model metadata.

 Roman1.1.0's override omits this base-library behavior. These edits live in
 working models only; the calibrated ASDF inputs are never rewritten.
 """
 def _assign_member_to_model(self, model, member):
  super()._assign_member_to_model(model, member)
  if 'group_id' in member:model.meta['group_id']=member['group_id']

def main():
 p=argparse.ArgumentParser(description=__doc__);root=Path(os.environ.get('ROMAN_REDUCTION_ROOT',str(Path(__file__).resolve().parent.parent)))/'F106'
 p.add_argument('--input-dir',type=Path,default=root/'stage2_flux');p.add_argument('--output-dir',type=Path,default=root/'stage3_60mas')
 p.add_argument('--product',default='Roman_ISim_F106_60mas_northup');p.add_argument('--run',action='store_true');p.add_argument('--in-memory',action='store_true',help='Keep input library and intermediate median stack in RAM; requires substantial RAM')
 p.add_argument('--detectors',nargs='+',type=int,default=list(range(1,19)),help='Detector numbers to include, e.g.1 2 3 4 5')
 a=p.parse_args();assert version('romancal')=='1.1.0','Review parameters after version changes'
 selected={f'WFI{i:02d}' for i in a.detectors};assert selected and all(1<=i<=18 for i in a.detectors)
 files=[f for f in sorted(a.input_dir.resolve().glob('r*_bkgsub_flux.asdf')) if f.name.split('_')[2].upper() in selected];assert len(files)==4*len(selected),f'Expected{4*len(selected)} inputs, found{len(files)}'
 detectors={};footprints=[]
 for f in files:
  with rdm.open(str(f)) as m:
   for step in ['photom','flat_field','tweakreg','flux']:assert m.meta.cal_step[step]=='COMPLETE',(f,step)
   assert m.meta.instrument.optical_element=='F106'
   d=m.meta.instrument.detector;detectors[d]=detectors.get(d,0)+1;footprints.append(m.meta.wcs.footprint())
 assert set(detectors)==selected and set(detectors.values())=={4}
 out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 asn=asn_from_list([str(f) for f in files],product_name=a.product)
 # Simulation observation_id is '?' for every file: preserve four independent exposures.
 for member in asn['products'][0]['members']:
  member['group_id']='isim_exposure_'+Path(member['expname']).name.split('_')[1]
 _,serialized=asn.dump();asnpath=out/(a.product+'_asn.json');asnpath.write_text(serialized)
 lib=ExposureGroupedLibrary(str(asnpath),on_disk=True)
 assert len(lib.group_indices)==4 and all(len(g)==len(selected) for g in lib.group_indices.values())
 wcs,scale,ratio=make_output_wcs(lib,pscale=.06/3600,rotation=0.,shape=None,crpix=None,crval=None)
 ny,nx=wcs.array_shape
 # Add an automatic two-pixel border against footprint-to-integer rounding.
 wcs,scale,ratio=make_output_wcs(lib,pscale=.06/3600,rotation=0.,shape=(ny+4,nx+4),crpix=None,crval=None)
 ny,nx=wcs.array_shape;x=(nx-1)/2;y=(ny-1)/2;c=SkyCoord(*wcs(x,y),unit='deg');up=SkyCoord(*wcs(x,y+1),unit='deg');right=SkyCoord(*wcs(x+1,y),unit='deg')
 pa=float(c.position_angle(up).deg);pa=(pa+180)%360-180
 assert abs(pa)<.01 and abs(c.separation(up).arcsec-.06)<1e-5
 for fp in footprints:
  xx,yy=wcs.invert(fp[:,0],fp[:,1],with_bounding_box=False);assert np.all(np.isfinite(xx)) and np.all(np.isfinite(yy));assert min(xx)>=-1 and max(xx)<=nx and min(yy)>=-1 and max(yy)<=ny, (nx,ny,min(xx),max(xx),min(yy),max(yy))
 asdf.AsdfFile({'wcs':wcs}).write_to(out/(a.product+'_planned_wcs.asdf'))
 pipeline=MosaicPipeline();pipeline.output_dir=str(out);pipeline.save_results=True;pipeline.on_disk=not a.in_memory;pipeline.resample_on_skycell=False
 pipeline.flux.skip=True;pipeline.skymatch.skip=True;pipeline.source_catalog.skip=True
 pipeline.outlier_detection.in_memory=a.in_memory
 pipeline.resample.in_memory=a.in_memory;pipeline.resample.rotation=0.;pipeline.resample.pixel_scale=.06;pipeline.resample.pixfrac=1.;pipeline.resample.kernel='square';pipeline.resample.weight_type='ivm';pipeline.resample.include_var_flat=True
 pipeline.resample.output_shape=[nx,ny];pipeline.resample.crpix=None;pipeline.resample.crval=None
 report=dict(inputs=len(files),detectors=detectors,romancal=version('romancal'),rotation=0.,pixel_scale_arcsec=scale,shape_yx=[ny,nx],center_radec_deg=[float(c.ra.deg),float(c.dec.deg)],measured_north_pa_deg=pa,measured_x_pa_deg=float(c.position_angle(right).deg),single_float32_plane_GiB=nx*ny*4/2**30,steps=dict(flux='skip: already complete',skymatch='skip: retain custom background',outlier_detection='run',resample='square/pixfrac1/ivm',source_catalog='skip'),in_memory=a.in_memory,mode='run' if a.run else 'prepare_only')
 (out/'mosaic_preflight.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
 if a.run:
  target=out/(a.product+'_coadd.asdf')
  if target.exists():raise FileExistsError(target)
  # Library scratch files live on the output volume, not the system temp partition.
  with tempfile.TemporaryDirectory(prefix='mosaic-scratch-',dir=out) as scratch:
   old=tempfile.tempdir;oldcwd=os.getcwd();tempfile.tempdir=scratch;os.chdir(scratch)
   try:
    runlib=ExposureGroupedLibrary(str(asnpath),on_disk=not a.in_memory)
    result=pipeline.run(runlib)
   finally:tempfile.tempdir=old;os.chdir(oldcwd)
  mosaic=result[0];assert mosaic.data.shape==(ny,nx)
  report['completed']=True;(out/'mosaic_completion.json').write_text(json.dumps(report,indent=2));print('MOSAIC COMPLETE',flush=True)
 else:print('Prepared only. Add --run to execute the mosaic.',flush=True)
if __name__=='__main__':main()
