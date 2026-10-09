"""Resumable, per-step Roman 1.1.0 imaging calibration through flatfield.

Each saved ASDF checkpoint includes the complete data model; JSON companions
record the execution boundary. No pixel-only FITS files are used for restart.
"""
from pathlib import Path
from datetime import datetime, timezone
from importlib.metadata import version
import argparse
import json
import os
import re
import logging
import tempfile

ORDER = ('dq_init', 'saturation', 'refpix', 'dark_decay', 'wfi18_transient',
         'linearity', 'rampfit', 'dark_current', 'assign_wcs', 'photom', 'flatfield')
STATUS = dict(zip(ORDER, ('dq_init', 'saturation', 'refpix', 'dark_decay',
    'wfi18_transient', 'linearity', 'ramp_fit', 'dark', 'assign_wcs', 'photom', 'flat_field')))


def receipt(path):
    return Path(str(path) + '.checkpoint.json')


def stat(path):
    s = Path(path).stat()
    return {'size': s.st_size, 'mtime_ns': s.st_mtime_ns}


def load_state(path):
    path = Path(path).resolve()
    if receipt(path).exists():
        state = json.loads(receipt(path).read_text())
        if state['file_stat'] != stat(path):
            raise ValueError('Checkpoint changed outside this workflow. Use save_custom() for edits.')
        if state['order'] != list(ORDER):
            raise ValueError('Checkpoint uses a different step order.')
        return state
    if not path.name.endswith('_uncal.asdf'):
        raise ValueError('Resume requires the checkpoint JSON alongside its ASDF.')
    return {'root': path.name.removesuffix('_uncal.asdf'), 'completed': [],
            'history': [], 'order': list(ORDER), 'original_input': str(path)}


def save_checkpoint(model, dest, state):
    """Save full ASDF atomically, then its restart receipt; never overwrite."""
    dest = Path(dest).resolve()
    if dest.exists() or receipt(dest).exists():
        raise FileExistsError(f'{dest}: use another output directory for a new branch.')
    dest.parent.mkdir(parents=True, exist_ok=True)
    model.meta.filename = dest.name
    # Keep the final basename when saving: Roman embeds it in metadata.
    with tempfile.TemporaryDirectory(prefix='.checkpoint-', dir=dest.parent) as scratch:
        temp = Path(scratch) / dest.name
        model.save(str(temp))
        temp.rename(dest)
    state['file_stat'] = stat(dest)
    receipt(dest).write_text(json.dumps(state, indent=2, default=str))
    return dest


def environment_check():
    if version('romancal') != '1.1.0':
        raise RuntimeError('This sequence is verified for romancal 1.1.0; review it before changing versions.')
    if os.environ.get('CRDS_OBSERVATORY') != 'roman' or os.environ.get('CRDS_SERVER_URL') != 'https://roman-crds.stsci.edu':
        raise RuntimeError('Activate roman and source procedure/roman_env.sh first.')
    context = os.environ.get('CRDS_CONTEXT', '')
    if not re.fullmatch(r'roman_\d+\.pmap', context) or not os.environ.get('CRDS_PATH'):
        raise RuntimeError('Set a Roman cache and a pinned Roman PMAP context.')


def run_until(input_file, stop, output_dir, config=None):
    """Run only the steps AFTER the input checkpoint, through stop inclusive.

    config maps step names to Step.call keyword arguments. CRDS step parameters
    remain enabled unless explicitly disabled. Changes require a new branch.
    """
    environment_check()
    from romancal.pipeline import ExposurePipeline
    from romancal.pipeline.exposure_pipeline import _is_fully_saturated
    import roman_datamodels as rdm
    state = load_state(input_file)
    config = config or {}
    unknown = set(config) - set(ORDER)
    if unknown:
        raise ValueError(f'Unknown steps: {unknown}')
    for options in config.values():
        if set(options) & {'save_results', 'output_file', 'output_dir', 'suffix'}:
            raise ValueError('Checkpoint filenames are managed by the workflow, not step options.')
    if state['completed'] != list(ORDER[:len(state['completed'])]):
        raise ValueError('Invalid checkpoint sequence.')
    first = len(state['completed']); last = ORDER.index(stop)
    if last < first:
        raise ValueError(f'{stop} is already complete; start a new branch from an earlier checkpoint.')
    if state.get('context') and state['context'] != os.environ['CRDS_CONTEXT']:
        raise ValueError('CRDS context changed mid-reduction; restart from the raw file in a new directory.')
    state.update(context=os.environ['CRDS_CONTEXT'], romancal=version('romancal'))
    current = Path(input_file).resolve()
    outdir = Path(output_dir).resolve()
    # Preflight destination collisions before doing any processing.
    destinations = {name: outdir / f'{i+1:02d}_{name}' / f"{state['root']}_{name}.asdf"
                    for i,name in enumerate(ORDER) if first <= i <= last}
    for dest in destinations.values():
        if dest.exists() or receipt(dest).exists():
            raise FileExistsError(dest)
    for name in ORDER[first:last+1]:
        model = result = None
        try:
            model = rdm.open(str(current))
            if model.meta.instrument.name != 'WFI' or model.meta.exposure.type != 'WFI_IMAGE':
                raise ValueError('This workflow supports WFI_IMAGE only.')
            if name == 'dq_init' and not isinstance(model, rdm.datamodels.ScienceRawModel):
                raise ValueError('Start dq_init from a ScienceRawModel, not a previously initialized ramp.')
            for prev in state['completed']:
                status = model.meta.cal_step.get(STATUS[prev], 'INCOMPLETE')
                if status not in ('COMPLETE', 'SKIPPED', 'N/A'):
                    raise ValueError(f'Input does not record finished {prev}: {status}')
            if name == 'refpix' and _is_fully_saturated(model):
                raise RuntimeError('Fully saturated exposure: stopped after saturation checkpoint; do not continue.')
            options = dict(config.get(name, {}))
            print(f'{current.name}: {name}', flush=True)
            result = ExposurePipeline.step_defs[name].call(model, save_results=False, **options)
            status = result.meta.cal_step.get(STATUS[name], 'INCOMPLETE')
            if status not in ('COMPLETE', 'N/A') and not (status == 'SKIPPED' and options.get('skip')):
                raise RuntimeError(f'{name} returned {status}; stopping instead of silently continuing.')
            state['completed'].append(name)
            state['history'].append({'step':name, 'status':status, 'input':str(current),
                'options':options, 'utc':datetime.now(timezone.utc).isoformat(),
                'references':dict(result.meta.ref_file)})
            current = save_checkpoint(result, destinations[name], state)
        finally:
            if result is not None and result is not model:
                result.close()
            if model is not None:
                model.close()
    return current


def save_custom(parent, destination, edit, description):
    """Branch a 2D checkpoint. edit(model) changes the full model in place.

    The caller supplies and validates the scientific correction and appropriate
    uncertainty propagation. No NIRCam template is assumed valid for Roman.
    """
    import roman_datamodels as rdm
    import numpy as np
    if not description.strip():
        raise ValueError('Describe the correction and uncertainty treatment.')
    if not receipt(parent).exists():
        raise ValueError('Custom edits require a workflow checkpoint.')
    state = load_state(parent)
    with rdm.open(str(parent)) as model:
        if model.data.ndim != 2:
            raise ValueError('This custom image hook is for 2D rate images only.')
        shape = model.data.shape
        statuses = dict(model.meta.cal_step)
        detector = model.meta.instrument.detector
        filt = model.meta.instrument.optical_element
        edit(model)
        if model.data.shape != shape or not np.issubdtype(model.data.dtype, np.floating):
            raise ValueError('Keep the original image shape and floating data type.')
        if dict(model.meta.cal_step) != statuses or model.meta.instrument.detector != detector or model.meta.instrument.optical_element != filt:
            raise ValueError('Custom correction must preserve step status and detector/filter identity.')
        state['history'].append({'custom': description, 'input':str(Path(parent).resolve()),
                                  'utc':datetime.now(timezone.utc).isoformat()})
        return save_checkpoint(model, destination, state)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path)
    p.add_argument('--stop',choices=ORDER,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--config',type=Path,help='JSON mapping step names to keyword arguments')
    p.add_argument('--plan',action='store_true')
    a=p.parse_args()
    state=load_state(a.input)
    if a.plan:
        first=len(state['completed']);last=ORDER.index(a.stop)
        if last<first: p.error('Stop step is already complete.')
        print('\n'.join(ORDER[first:last+1]));return
    a.output_dir.mkdir(parents=True,exist_ok=True)
    handler=logging.FileHandler(a.output_dir/'staged.log')
    logging.getLogger().addHandler(handler)
    try:
        print(run_until(a.input,a.stop,a.output_dir,json.loads(a.config.read_text()) if a.config else None))
    finally:
        logging.getLogger().removeHandler(handler);handler.close()

if __name__=='__main__':
    main()


def step_main(name):
    """CLI shared by the SBWFI_01 ... SBWFI_11 single-step scripts."""
    p=argparse.ArgumentParser(description=f'Run ONLY Roman {name}; save every full-model intermediate.')
    p.add_argument('filter',nargs='?',default='F106')
    p.add_argument('--root',type=Path,default=Path.cwd())
    p.add_argument('--input',type=Path,help='One input; also accepts a custom checkpoint with its receipt')
    p.add_argument('--output-dir',type=Path,help='Checkpoint tree; defaults to FILTER/exposure_steps')
    p.add_argument('--config',type=Path)
    p.add_argument('--limit',type=int)
    p.add_argument('--plan',action='store_true')
    a=p.parse_args()
    index=ORDER.index(name)
    out=a.output_dir or a.root/a.filter/'exposure_steps'
    if a.input:
        inputs=[a.input]
    elif index == 0:
        inputs=sorted((a.root/a.filter/'stage1').glob('*_uncal.asdf'))
    else:
        prev=ORDER[index-1]
        inputs=sorted((out/f'{index:02d}_{prev}').glob(f'*_{prev}.asdf'))
    inputs = [f for f in inputs if not f.name.startswith('.')]
    if a.limit is not None:
        if a.limit<1: p.error('--limit must be positive')
        inputs=inputs[:a.limit]
    if not inputs: p.error('No inputs found; run the preceding step or supply --input.')
    for f in inputs:
        if len(load_state(f)['completed'])!=index:
            p.error(f'{f} is not the checkpoint immediately before {name}.')
    if a.plan:
        for f in inputs: print(f'{name}: {f} -> {out}')
        return
    config=json.loads(a.config.read_text()) if a.config else None
    out.mkdir(parents=True,exist_ok=True)
    handler=logging.FileHandler(out/f'{index+1:02d}_{name}.log')
    logging.getLogger().addHandler(handler)
    try:
        for f in inputs: print(run_until(f,name,out,config))
    finally:
        logging.getLogger().removeHandler(handler);handler.close()
