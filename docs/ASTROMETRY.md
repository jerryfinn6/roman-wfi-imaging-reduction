# SBWFI_13: SExtractor-to-truth tweakreg test

Run `bash SBWFI_13_do_astrometry.sh` under this procedure directory. The wrapper activates roman, sources roman_env.sh and retains a dated log with pipefail (failures propagate). Default test: first exposure WFI01, WFI07, WFI14. `--all` explicitly processes all72. The Python script supports --root, --catalog-dir, --truth and --output-dir; defaults reference the workspace outputs and SSD inputs. When copying to another location, supply those paths explicitly.

Uses romancal1.1.0, context roman_0072.pmap, existing SExtractor4σ selected catalogs. Their windowed xcentroid/ycentroid already equal XWIN/YWIN minus1; no second subtraction is performed. New x/y ECSV adapter catalogs are attached through meta.source_catalog.tweakreg_catalog_name. Single-frame ModelLibrary inputs implement SBNRC_05's independent absolute alignment. Original flatfields, SExtractor catalogs and supplied simulation cal files are unchanged. Aligned full ASDFs are separate outputs, with science/error/DQ/variance arrays verified unchanged.

Reference: outputs/full_catalog.ecsv, the I-Sim full_catalog.ecsv from the public stpubdata Roman roman-2026.2 tutorial_data directory. Only type=PSF is used, with finite RA/Dec and a0.20degree radius around the initial detector center. RA/DEC remain in degrees. No Gaia query, proper-motion correction, or reference-coordinate fitting is applied.

The first attempt mirrored SBNRC_05's search3arcsec, tolerance0.1arcsec, separation0.2arcsec, minimum10, nclip1 and sigma0.7, with explicit absolute shift geometry. It failed to match. Diagnostic comparison: original supplied WFI01 cal WCS matches truth at median0.0162arcsec, whereas the newly reduced WCS differs from supplied cal by approximately -36.75arcsec RA*cosDec and -184.71arcsec Dec, varying by about0.7arcsec across the detector. This indicates a WCS compatibility issue between these simulated inputs and the reduction/reference setup; it is not evidence of ordinary pointing error, and the exact reference responsible has not been isolated.

Test settings therefore use abs_searchrad=240arcsec, abs_tolerance=0.5arcsec, abs_separation=1arcsec, abs_fitgeometry=general (affine), abs_minobj=10, abs_nclip=3, abs_sigma=3, abs_use2dhist=True. Wider matching captures the large offset; affine fitting allows the observed spatial variation;3sigma clipping avoids the original aggressive0.7sigma clip. Relative settings retain the NIRCam values but are unused for single-frame runs. Although Roman internally enables expand_refcat with a custom reference, absolute_align passes expand_refcat=False.

Validation uses unique nearest truth matches within0.1arcsec AFTER alignment and compares those SAME pairs before/after. This is an in-sample residual diagnostic, not independent accuracy or completeness validation; do not interpret pre-fit nearest-neighbor distances as pointing errors. Fit status, match counts, transformation and residuals are retained in JSON/ECSV. GWCS inverse checks use interior positions and a0.01pixel tolerance; the inverse can differ from the forward transform by approximately0.001pixel after correction. No resampling or image coaddition is performed. Residual distortion beyond an affine correction may remain.

## Test results

| Detector | Fit matches | Validation pairs | Before median (arcsec) | After median (mas) | After P90 (mas) |
|---|---:|---:|---:|---:|---:|
| wfi01 | 1530 | 1560 | 188.330 | 16.16 | 24.29 |
| wfi07 | 1493 | 1503 | 192.063 | 16.38 | 27.12 |
| wfi14 | 420 | 1506 | 184.786 | 17.56 | 34.57 |

All three fit statuses SUCCESS; all saved models COMPLETE. Science arrays unchanged. Validated interior WCS roundtrip errors below0.002pixel. Only these three frames were aligned; remaining69 have not been processed.

## All72 completed

{
  "frames": 72,
  "median_residual_mas_range": [
    14.406469293279153,
    22.99744700910946
  ],
  "validation_matches_range": [
    1319,
    2445
  ],
  "fit_matches_range": [
    389,
    1864
  ],
  "roundtrip_max_pixel": 0.0038052171232575596
}
All72 fit receipts passed. The preceding three-frame-only statement describes the pilot, now superseded. Residuals use post-fit unique pairs within0.1arcsec and are not independent validation.
