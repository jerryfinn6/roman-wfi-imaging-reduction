**Run completed:** all 72 exposures reached flatfield on 2026-09-25. See [COMPLETION.md](COMPLETION.md) for validation and remaining quality issues. Earlier preparation/test notes below describe setup history.

# Roman I-Sim reduction: input sorting and CRDS preparation

Run in the `roman` Conda environment. This procedure adapts
`SBNRC_00_sort_uncals.py`: Roman uses `roman.meta.instrument.optical_element`
in ASDF instead of FITS `FILTER`.

## Working directory

`/path/to/Roman_I-Sim_reduction/`

- `uncal/`: incoming uncalibrated downloads (left in place for future arrivals).
- `F106/stage1/`: sorted uncalibrated ASDF cubes; all 18 detectors, four exposures.
- `cal/`: supplied calibrated simulation products, retained for comparison.
- `procedure/`: copies of these scripts.
- `crds_cache/`: Roman-only mappings and reference files.
- `logs/`: timestamped sorting manifests and CRDS logs.

## Commands

```bash
conda activate roman
cd /path/to/Roman_I-Sim_reduction
# Refresh settings if this terminal was already in roman before setup:
source procedure/roman_env.sh

# Inspect then apply sorting of any newly downloaded files:
python procedure/SBWFI_00_sort_uncals.py
python procedure/SBWFI_00_sort_uncals.py --apply

# Fetch references selected from sorted ASDF metadata:
bash procedure/SBWFI_00_sync_refs.sh
```

Equivalent direct CRDS command for this filter:

```bash
crds sync --roman --contexts "$CRDS_CONTEXT" --fetch-references \
  --dataset-files F106/stage1/*_uncal.asdf
```

The wrapper refuses an empty dataset list, avoiding an unintended whole-context
reference download. The sorter checks imaging mode, filter, 3D data shape, and
collisions before moving inputs. It ignores `.part` downloads. It is safe to
rerun after a successful sort. It never overwrites a same-named destination.
Only downloaders that finalize by renaming `.part` to `.asdf` should write into
`uncal/` while sorting. Re-running the original bulk downloader after moving
files may redownload them; check `F106/stage1/` before doing so.

## Environment and reproducibility

`roman` activation hooks select:

```bash
export CRDS_PATH=/path/to/Roman_I-Sim_reduction/crds_cache
export CRDS_SERVER_URL=https://roman-crds.stsci.edu
export CRDS_OBSERVATORY=roman
export CRDS_CONTEXT=roman_0072.pmap
```

Deactivation restores the previous values, including prior JWST settings.
The context is explicitly pinned; it is not a floating latest-context alias.

The original images record context `roman_0055.pmap` and the supplied calibrated
images record `romancal 1.0.1`. A synchronization attempt under that context
failed because CRDS now marks some recommended references scientifically
invalid. We did not override those checks. The selected baseline is instead
`romancal 1.1.0` with operational context `roman_0072.pmap`, obtained from the
Roman CRDS server on 2026-09-25. Expect possible calibration differences from
the supplied L2 images. Installed versions are recorded in `requirements.txt`.

Sorting and reference synchronization do not execute ExposurePipeline or modify
pixel arrays. The next stage is an initial single-exposure calibration test,
followed by inspection before processing the full set.

## Documentation

- https://roman-docs.stsci.edu/data-handbook/roman-wfi-data-pipelines
- https://roman-docs.stsci.edu/data-handbook/roman-wfi-data-pipelines/exposure-level-pipeline
- https://roman-crds.stsci.edu/static/users_guide/command_line_tools.html

## Staged calibration scripts

See [STAGED_REDUCTION.md](STAGED_REDUCTION.md) for SBWFI_01 through SBWFI_11, restart semantics, custom branches, and the notebook. These scripts are prepared but have not yet been run on full-size science exposures.


Future reduction order (user preference): run PHOTOM and then FluxStep immediately, before subsequent background subtractions. See FLUX.md. Current historical checkpoint order and DN/s products are preserved.
