# Move to a larger-memory machine

Minimum folder layout (retain these relative paths; parent folder can be renamed):

```
Roman_I-Sim_reduction/
  procedure/                         # scripts, requirements, manifest, documentation
  F106/stage2_flux/                   # all72 *_bkgsub_flux.asdf files and receipts
```

Copying the entire reduction folder is also fine. Earlier raw/calibration/background stages and truth/source catalogs are not needed to run the final mosaic. Keep those elsewhere for reproducibility. The final enabled outlier/resample steps have no CRDS reference-file requirements in romancal1.1.0; the old cache is not required for this final-only run. The runner retains the pinned context for provenance. Associations from this Mac contain old paths: do not reuse them; the script rebuilds the association on the new machine.

Set up the environment on the destination (do not copy the Mac Conda directory to Linux):

```bash
conda create -n roman python=3.12 pip
conda activate roman
cd /new/path/Roman_I-Sim_reduction
python -m pip install -r procedure/mosaic_requirements.txt
python -m pip check
python procedure/verify_mosaic_transfer.py
bash procedure/SBWFI_16_do_mosaic.sh
```

The last command is a preparation-only check: verifies72flux-calibrated inputs,18detectors×4exposures, required calibration statuses, exposure grouping and output north-up WCS/scale/footprint. Review F106/stage3_60mas/mosaic_preflight.json. Nothing has been drizzled yet.

Then run either disk-backed (default):

```bash
bash procedure/SBWFI_16_do_mosaic.sh --run
```

or fully in-memory input/intermediate handling:

```bash
bash procedure/SBWFI_16_do_mosaic.sh --run --in-memory
```

The expected peak RAM is an estimate, not measured: roughly160–240GiB; allow384–512GiB for headroom. Disk mode still needs large output arrays. Keep substantial free scratch/output space (several hundred GiB advisable). The script has never completed a full drizzle run; the destination preflight and runtime are still required. Core package versions are pinned to the tested environment. Full original pip snapshot is included for dependency troubleshooting; cross-platform installation has not been tested.

Output: F106/stage3_60mas/Roman_ISim_F106_60mas_northup_coadd.asdf. Logs: logs/mosaic_*.log. Defaults resolve relative to procedure/, with optional ROMAN_REDUCTION_ROOT, ROMAN_PYTHON or CLI input/output path overrides. No /Users/... Conda activation or /Volumes/... mount paths are required by the final runner.

The full mosaic retains the current background strategy, flux unitsMJy/sr, zero-based astrometry, outlier rejection and north-up0.06arcsec output. Flux/skymatch/catalog steps skipped; no new astrometric fit. Review WFI14 galaxy outskirts in the resulting mosaic before choosing any new subtraction strategy.


## Validated subset run, 2026-09-25

20 frames, four exposure groups of five detectors. Outlier detection and resample COMPLETE. Saved coadd: SSD F106/stage3_WFI01_05_60mas/Roman_ISim_F106_WFI01_05_60mas_coadd.asdf (about9GB). Shape30082×20258, north-up, measured scale0.05999999997arcsec/pixel. 479930620 positive-weight pixels (78.754%coverage), all with finite science. Five covered pixels have nonfinite uncertainties; exclude them from uncertainty-based measurements. var_flat is entirely NaN because these inputs do not supply that component; errors combine available components and do not include background-estimation uncertainty. Variance reconstruction generated warnings; no silent repair was applied. Coadd flux status SKIPPED is expected: its inputs already had FluxStep COMPLETE and remain in MJy/sr.

Initial failure was corrected by propagating explicit association group IDs into working model metadata via ExposureGroupedLibrary. Input images/timestamps preserved. All simulation timestamps coincide; group assignments preserve the four distinct exposures. Actual20-frame runtime now passed; the full72-frame mosaic remains unexecuted. This confirms execution and basic product validity, not independent photometric/astrometric accuracy. Existing WFI14 background caveat remains relevant to the later full mosaic.

Inspected reduced-size science preview and generated weight preview; detector geometry/gaps visible. Detailed pixel counts in validation.json. Embedded calibration logs contain repeated copies of all frame messages; deduplicated by complete log line, not by numerical count.

Outlier flags: 20 per-frame messages, 3934–42307 pixels/frame, total 533627.

## Step 17: export FITS after drizzling

```bash
python procedure/SBWFI_17_asdf_to_fits.py \
  F106/stage3_60mas/Roman_ISim_F106_60mas_northup_coadd.asdf \
  --output-dir F106/stage3_60mas/fits
```

See FITS_EXPORT.md for array contents, WCS validation, units and retained limitations.
