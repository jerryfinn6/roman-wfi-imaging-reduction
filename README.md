# Roman WFI imaging reduction

Staged SBWFI imaging procedures developed using Roman I-Sim F106 simulations. Imaging only; not grism/prism spectroscopy. This is a research workflow, not a flight-data calibration recommendation.

## Contents

- `procedure/`: calibration and analysis steps 00–17, notebook and helpers.
- `sextractor/`: preferred 4-sigma catalog extraction and configuration.
- `utilities/`: download, preview and background diagnostics.
- `docs/`: detailed procedure and I-Sim validation notes.

## Environment

```bash
conda create -n roman python=3.12 pip
conda activate roman
python -m pip install -r requirements.txt
python -m pip check
```

`requirements.txt` pins the core pipeline plus preview/download dependencies. `requirements-full-snapshot.txt` preserves all packages from the original environment (including optional simulation tools); it is not a cross-platform lockfile. SExtractor is a separate system executable: install it using your platform's package manager and set the executable path in `sextractor/SBWFI_12_test_sextractor.py`. This repository does not install it through pip.

## Configure before running

Earlier stages are research templates with explicit `/path/to/` placeholders, F106/72-frame assumptions and output conventions. Review each script's arguments and paths before execution. Search with `rg '/path/to|/opt/homebrew' procedure sextractor utilities`. Configure `roman_env.sh` with your cache; it pins `roman_0072.pmap` and the Roman CRDS server. Supply your own inputs and truth catalog. Never run the entire set blindly.

The final mosaic and FITS runners accept portable paths. Copy `procedure/` into your reduction root alongside `F106/stage2_flux/` (72 prepared ASDF images). From that root:

```bash
conda activate roman
bash procedure/SBWFI_16_do_mosaic.sh
bash procedure/SBWFI_16_do_mosaic.sh --run --in-memory
python procedure/SBWFI_17_asdf_to_fits.py \
  F106/stage3_60mas/Roman_ISim_F106_60mas_northup_coadd.asdf \
  --output-dir F106/stage3_60mas/fits
```

The first command is preflight only. Omit `--in-memory` for disk-backed inputs; output arrays still require substantial RAM. Full 72-image peak RAM was estimated at 160–240 GiB, not measured; allow 384–512 GiB headroom. Output is north-up, 0.06 arcsec/pixel, automatic footprint.

## Step map

| Step | Operation |
|---|---|
| 00 | Sort uncalibrated images and synchronize CRDS references |
| 01–06 | DQ initialization, saturation, reference pixels, dark decay, WFI18 transient, linearity |
| 07–11 | Ramp fit, dark current, WCS, PHOTOM metadata, flat field |
| 12 | Source catalog: SExtractor preferred; photutils comparison retained |
| 13 | Truth-reference astrometry |
| 14 | Per-detector 2D background subtraction |
| 15 | Flux conversion |
| 16 | Outlier rejection and drizzle mosaic |
| 17 | ASDF arrays to FITS with checked celestial WCS |

Historical numbering preserves the tested checkpoints. Future reductions should place FluxStep immediately after PHOTOM; do not reinterpret or silently reorder existing checkpoints. SExtractor windowed coordinates are converted to zero-based exactly once.

## Validation and limitations

All 72 frames completed astrometry, background subtraction and flux conversion in the original workflow. Actual outlier rejection plus drizzle succeeded for WFI01–05 (20 frames); full 72-frame drizzling has not been executed. The subset FITS export passed exact pixel/checksum checks. Packaging changes have syntax validation only, not a fresh scientific run.

Large initial WCS offsets remain an unresolved simulation/reference compatibility issue. Existing background masks can subtract extended galaxy outskirts. Background-estimate uncertainties are not propagated; flat variance is absent, and five covered subset mosaic pixels have invalid errors. Read the detailed docs before science use. No science data, reference cache, credentials or local run receipts are shipped.

## Collaboration and licensing

See CONTRIBUTING.md and UPLOAD.md. No software license has been selected by the owner yet. Select a license before public redistribution; retain third-party notices in the SExtractor configuration resources. This repository does not grant licenses to upstream packages or data.
