# Roman staged reduction complete — 2026-09-25

All 72 F106 exposures (four exposures × WFI01–18) completed through flatfield.
The batch exited with code 0. Each of the 11 checkpoint directories contains
72 science ASDF files and corresponding restart receipts: 792 checkpoints total.
Hidden macOS `._` files are filesystem metadata, not additional science products.

Final files:
`/path/to/Roman_I-Sim_reduction/F106/exposure_steps/11_flatfield/r*_flatfield.asdf`

Intermediate files: the sibling `01_dq_init` through `10_photom` directories.
Science checkpoints occupy approximately 146.35 GB. Original raw inputs and
supplied `cal/` products were preserved.

## Configuration and verification

- Conda environment: roman; romancal 1.1.0; CRDS context roman_0072.pmap.
- CRDS synchronization: 329 references plus 15 mappings; 0 errors and 0 warnings.
- Full-size outputs: 4088 × 4088; expected calibration statuses present.
- WFI18 transient correction complete for WFI18, N/A for other detectors.
- Positive finite photometric conversion factors; DQ, errors and variance arrays present.
- WCS round-trip checks at three positions per image: maximum error below 4e-7 pixels.
  This checks coordinate-transform consistency, not absolute astrometric accuracy.
- Every image has more than 99.99% finite science pixels.

## Remaining quality issues

Each image has 25–449 nonfinite science pixels without the DO_NOT_USE bit set.
Each has 26–449 nonfinite errors without that bit, and 37–2626 negative errors.
All negative errors carry other nonzero DQ flags; none occur in DQ=0 pixels.
These are retained upstream calibration outputs, not silently repaired. Review
DQ selection, nonfinite values and uncertainties before scientific measurements.
Passing the structural checks does not establish science-ready photometry.
No source_catalog, tweakreg, mosaicking or custom artifact correction was run.

The first exposure retains a harmless stored `.partial.asdf` filename mismatch
from the original atomic-save implementation; reopening repairs this in memory.
The implementation was corrected for subsequent exposures. Pixel arrays were not
changed to resolve that warning. Input discovery now excludes macOS metadata files.

Detailed per-image validation: `batch_status.json`. The procedure scripts and
notebook remain available to repeat or branch individual steps.
