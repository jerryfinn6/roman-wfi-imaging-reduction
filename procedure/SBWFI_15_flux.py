#!/usr/bin/env python3
"""Apply Roman FluxStep once; for future reductions run immediately after PHOTOM."""
from pathlib import Path
import argparse,json,tempfile
import numpy as np
import roman_datamodels as rdm
from romancal.flux import FluxStep

def main():
 p=argparse.ArgumentParser(description=__doc__);base=Path('/path/to/work/outputs')
 p.add_argument('--input-dir',type=Path,default=base/'roman_background');p.add_argument('--output-dir',type=Path,default=base/'roman_flux');p.add_argument('--pattern',default='r*_bkgsub.asdf')
 a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True);reports=[]
 for path in sorted(a.input_dir.glob(a.pattern)):
  target=a.output_dir/(path.stem+'_flux.asdf');receipt=target.with_suffix('.json')
  if target.exists() and receipt.exists():reports.append(json.loads(receipt.read_text()));continue
  if target.exists():raise RuntimeError(f'Unvalidated output {target}')
  with rdm.open(str(path)) as m:
   assert m.meta.cal_step.photom=='COMPLETE'
   if m.meta.cal_step.flux=='COMPLETE':raise ValueError('Input already flux calibrated')
   c=float(m.meta.photometry.conversion_megajanskys);assert np.isfinite(c) and c>0
   result=FluxStep.call(m,save_results=False);result.meta.filename=target.name
   with tempfile.TemporaryDirectory(dir=a.output_dir) as tmp:
    temp=Path(tmp)/target.name;result.save(str(temp));temp.rename(target)
  with rdm.open(str(path)) as original,rdm.open(str(target)) as saved:
   for name in ['data','err','var_poisson','var_rnoise','var_flat']:
    if hasattr(original,name):
     factor=c if name in ['data','err'] else c*c
     assert np.allclose(getattr(saved,name),getattr(original,name)*factor,rtol=2e-6,atol=0,equal_nan=True),name
   assert np.array_equal(saved.dq,original.dq)
   x=np.array([10.,2043.,4077.]);assert np.allclose(saved.meta.wcs(x,x),original.meta.wcs(x,x));assert saved.meta.cal_step.flux=='COMPLETE'
  info=dict(input=str(path),output=str(target),conversion=c,units='MJy/sr',validation='data/error/variance scaling, DQ and WCS verified',flux_status='COMPLETE');receipt.write_text(json.dumps(info,indent=2));reports.append(info);print(json.dumps(info),flush=True)
 (a.output_dir/'summary.json').write_text(json.dumps(reports,indent=2));print('COMPLETE',len(reports),flush=True)
if __name__=='__main__':main()
