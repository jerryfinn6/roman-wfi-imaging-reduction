"""Sequential, resumable batch through flatfield; one subprocess per exposure."""
from pathlib import Path
import json, subprocess, sys, os, shutil, fcntl, traceback
from datetime import datetime,timezone
from roman_staged import ORDER, STATUS, load_state
ROOT=Path('/path/to/Roman_I-Sim_reduction')
OUT=ROOT/'F106/exposure_steps'
HERE=Path(__file__).resolve().parent
STATUS_FILE=HERE/'batch_status.json'

def validate(path):
    import roman_datamodels as rdm
    import numpy as np
    with rdm.open(str(path)) as m:
        assert m.data.shape==(4088,4088)
        statuses=dict(m.meta.cal_step)
        for step in ORDER:
            assert statuses[STATUS[step]] == ('N/A' if step=='wfi18_transient' and m.meta.instrument.detector!='WFI18' else 'COMPLETE'), (step,statuses)
        a=np.asarray(m.data); good=(m.dq & 1)==0
        finite=np.isfinite(a)
        assert finite.mean()>.99, 'Too many nonfinite pixels'
        assert m.err.shape==a.shape and m.dq.shape==a.shape
        assert np.all(m.err[(m.dq==0)&np.isfinite(m.err)]>=0), 'Negative errors in DQ=0 pixels'
        phot=float(m.meta.photometry.conversion_megajanskys)
        assert np.isfinite(phot) and phot>0
        x=np.array([500.,2044.,3500.]); y=np.array([500.,2044.,3500.])
        ra,dec=m.meta.wcs(x,y); assert np.all(np.isfinite(ra)) and np.all(np.isfinite(dec))
        xx,yy=m.meta.wcs.numerical_inverse(ra,dec)
        residual=float(np.max(np.hypot(xx-x,yy-y))); assert residual<.01
        var={k: {'shape':list(np.asarray(m[k]).shape),'finite_fraction':float(np.isfinite(m[k]).mean())} for k in m if k.startswith('var_')}
        report={'path':str(path),'shape':list(a.shape),'finite_fraction':float(finite.mean()),
                'nonfinite_not_do_not_use':int(np.count_nonzero(~finite&good)),
                'bad_error_not_do_not_use':int(np.count_nonzero((~np.isfinite(m.err))&good)),
                'negative_errors':int(np.count_nonzero(m.err<0)),
                'negative_errors_dq_zero':int(np.count_nonzero((m.err<0)&(m.dq==0))),
                'wcs_roundtrip_max_pixels':residual,'conversion_megajanskys':phot,'cal_step':statuses,
                'variances':var,'median_dn_per_second':float(np.nanmedian(a))}
        assert var, 'Missing variance arrays'
        return report

def save(state):
    state['updated_utc']=datetime.now(timezone.utc).isoformat()
    tmp=STATUS_FILE.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2));tmp.replace(STATUS_FILE)

if __name__=='__main__':
    lock=open(HERE/'batch.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    files=sorted(f for f in (ROOT/'F106/stage1').glob('*_uncal.asdf') if not f.name.startswith('.'));assert len(files)==72
    state={'phase':'running','pid':os.getpid(),'completed':[],'total':len(files),'reports':[]}
    try:
        for raw in files:
            state['current']=raw.name;save(state)
            if shutil.disk_usage(ROOT).free<30*2**30:raise RuntimeError('Less than 30 GiB free; stopping before another exposure')
            stem=raw.name.removesuffix('_uncal.asdf');current=raw
            for i,step in enumerate(ORDER,1):
                check=OUT/f'{i:02d}_{step}'/f'{stem}_{step}.asdf'
                if not check.exists():break
                s=load_state(check);assert s['completed']==list(ORDER[:i]);current=check
            if len(load_state(current)['completed'])<len(ORDER):
                log=ROOT/'logs'/f'{stem}_staged.log'
                with log.open('a') as stream:
                    subprocess.run([sys.executable,str(HERE/'roman_staged.py'),str(current),'--stop','flatfield','--output-dir',str(OUT),'--config',str(HERE/'step_options.json')],stdout=stream,stderr=subprocess.STDOUT,check=True)
            final=OUT/'11_flatfield'/f'{stem}_flatfield.asdf'
            report=validate(final)
            state['reports'].append(report);state['completed'].append(raw.name);save(state)
            print(f'Validated {len(state["completed"])}/72: {raw.name}',flush=True)
        state['phase']='complete';save(state)
    except BaseException:
        state['phase']='failed';state['error']=traceback.format_exc();save(state);raise
