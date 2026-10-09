**Run completed:** all 72 exposures reached flatfield on 2026-09-25. See [COMPLETION.md](COMPLETION.md) for validation and remaining quality issues. Earlier preparation/test notes below describe setup history.

# SBWFI: restartable exposure calibration

This follows the executed order in **romancal 1.1.0**, checked against
`ExposurePipeline._process_model` and the [official exposure documentation](https://roman-pipeline.readthedocs.io/en/stable/roman/pipeline/exposure_pipeline.html).
The NIRCam comparison used `SBNRC_01_stage1.py`, `SBNRC_02_stage2med_SW.py`,
`SBNRC_02_stage2_LW.py`, and `SBNRC_SWimaging_pipeline.ipynb`.

## Scripts and order

| Script | Operation / checkpoint |
|---|---|
| `SBWFI_00_sort_uncals.py` | Sort incoming uncalibrated ASDF by metadata filter |
| `SBWFI_00_sync_refs.sh` | Fetch CRDS references; separate from sorting |
| `SBWFI_01_dq_init.py` | Initialize DQ and convert raw input to a working ramp |
| `SBWFI_02_saturation.py` | Flag saturated ramp samples |
| `SBWFI_03_refpix.py` | Reference-pixel correction |
| `SBWFI_04_dark_decay.py` | Time-dependent dark decay correction |
| `SBWFI_05_wfi18_transient.py` | WFI18 first-read correction; N/A on other detectors |
| `SBWFI_06_linearity.py` | Nonlinearity correction |
| `SBWFI_07_rampfit.py` | Ramp fitting and associated jump handling; 3D to 2D |
| `SBWFI_08_dark_current.py` | Subtract dark current from the rate image |
| `SBWFI_09_assign_wcs.py` | Assign distortion-aware WCS; not fitted astrometric alignment |
| `SBWFI_10_photom.py` | Attach photometric conversion factors |
| `SBWFI_11_flatfield.py` | Flat-field the image and uncertainties |

Scripts 01–08 provide the detector-calibration block analogous to your NIRCam
stage 1. Scripts 09–11 provide the image-calibration block. This is a conceptual
comparison: Roman's dark-current step follows ramp fitting, and photom precedes
flatfield. Jump handling is part of rampfit, not a separate JWST-style JumpStep.
Do not copy NIRCam jump/snowball thresholds without testing Roman-specific options.

Roman photom records conversion metadata; it does **not** scale the pixel array
into MJy/sr. These rate images stay in DN/s. Completing step 11 therefore includes
both photometric metadata and flat-fielding. It is not a full official ELP run:
source extraction, tweakreg, and their additional products are deliberately deferred.

## First-exposure trial, after reference download

```bash
conda activate roman
cd /path/to/Roman_I-Sim_reduction
source procedure/roman_env.sh
python procedure/SBWFI_01_dq_init.py F106 --limit 1 --plan
python procedure/SBWFI_01_dq_init.py F106 --limit 1
python procedure/SBWFI_02_saturation.py F106 --limit 1
# Then run 03, 04, ... 11 individually, inspecting checkpoints as desired.
```

Without `--limit`, each script processes all available inputs in sequence. It stops
on the first failure with a traceback; no failures are silently discarded.
Script 01 reads `F106/stage1/*_uncal.asdf`. Subsequent scripts read the preceding
checkpoint directory. Use `--input /absolute/path/to/checkpoint.asdf` for a selected
exposure or custom branch. `--output-dir` selects a new checkpoint tree.

Every step writes a complete ASDF model under
`F106/exposure_steps/NN_step/`, plus `.asdf.checkpoint.json` and a step log.
The model preserves DQ, error/variance arrays, reference metadata and WCS where
present. The JSON records step history, explicit options, context, references,
source path and a size/mtime guard. Keep ASDF and JSON together. The size/mtime
check is not a cryptographic integrity check. Existing products are not overwritten.
A restart uses the previous valid checkpoint; rerunning an already completed step
is rejected. To compare parameter choices, branch from its predecessor into a new
`--output-dir`. The supplied `cal/` products are never overwritten.

The code requires romancal 1.1.0 and a pinned Roman context. Missing-reference skips
are treated as failures unless `skip: true` was explicitly requested. Fully
saturated data stop after the saturation checkpoint rather than following the
full pipeline's zero-image shortcut. The checkpoint remains available for inspection.

## Custom corrections: two useful boundaries

1. **After 08 dark_current, before flatfield**: a detector-rate correction; WCS
   can also be assigned first by pausing after 09.
2. **After 11 flatfield**: a flat-fielded image correction, similar to your
   NIRCam flatfield/wisp inspection branch. Photometric conversion factors are
   already attached; do not run flatfield or photom again merely to finish a branch.

Use the notebook or Python helper to save a separate custom checkpoint:

```python
from pathlib import Path
from roman_staged import save_custom, run_until

parent = Path('/absolute/path/to/dark_current_checkpoint.asdf')

def correction(model):
    # Supply a Roman-appropriate model with matching shape, pixel frame and DN/s units.
    # model.data -= correction_dn_per_second
    # Propagate uncertainty and preserve/update DQ as scientifically required.
    raise NotImplementedError('Implement and validate the scientific correction first.')

custom = save_custom(parent, '/absolute/path/to/custom_rate.asdf', correction,
                     'Describe correction, template/version, amplitude, and uncertainty handling.')
# Resume only AFTER the parent's completed step:
final = run_until(custom, 'flatfield', '/absolute/path/to/corrected_branch')
```

The unedited checkpoint stays intact. The custom hook preserves the completed-step
boundary, records the description, and requires unchanged detector/filter, shape
and calibration status. It does not implement a wisp model or certify a user
correction. NIRCam templates are not assumed applicable to Roman. Your NIRCam
notebook estimates backgrounds on flat-fielded images and sometimes applies them
back to rate images: any analogous Roman operation must account for the flat-field
transformation rather than silently mixing the two pixel domains.

## Step parameters

Pass `--config step_options.json` with a dictionary keyed by step name, e.g.:

```json
{"rampfit": {"maximum_cores": "1"}}
```

The runnable scripts use the individual STPipe Step.call interfaces, so CRDS step
parameter lookup remains enabled by default; explicit options override defaults.
No automatic full-frame batch calibration has been started while reference
synchronization is in progress. Full-size science validation remains to be done.
Saving six full ramp checkpoints for all 72 exposures will require substantial
additional disk space; measure the first-exposure output sizes before a full batch.

## Validation performed

Small synthetic data with local test references successfully exercised actual DQ initialization and saturation, ASDF checkpoint reopening, continuation at the next step, rejection of repeated steps, and a custom 2D branch that preserves its parent and error array. The CLI plan selected the expected first WFI01 input. All scripts and notebook cells passed syntax checks. Full-detector calibration through flatfield is not yet validated; wait for the reference download and begin with one exposure.

The optional notebook requires a Jupyter kernel using the roman interpreter; the notebook file itself does not install or register a kernel.


Future reduction order (user preference): run PHOTOM and then FluxStep immediately, before subsequent background subtractions. See FLUX.md. Current historical checkpoint order and DN/s products are preserved.
