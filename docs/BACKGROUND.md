# SBWFI_14 per-detector background subtraction

Run with roman Python: `python SBWFI_14_background.py`. Inputs default to workspace outputs/roman_tweakreg_test; outputs to outputs/roman_background. Supports --input-dir, --output-dir and --limit. Each ASDF detector frame has its own model; no exposure stacking or cross-detector estimation.

Matches the executed parameters in SBNRC_03: detect_threshold3sigma;10connected pixels; circular source-mask dilation radius10; SigmaClip3sigma,maxiters10; MedianBackground;128pixel mesh;5×5mesh median filter; exclude_percentile80. Zero values are excluded from estimation as in NIRCam. Nonfinite science/errors, nonpositive errors and DNU pixels are additionally excluded. Original zero/invalid science values are not replaced for science output; science=data-background. Source masking and sigma clipping exclude sources when estimating the background, not when subtracting it.

Saves full bkgsub ASDF, pixel-aligned background FITS with background RMS and estimation mask extensions, JSON receipt, and3panel preview. FITS has no celestial WCS; companion ASDF preserves GWCS. Background RMS is local pixel scatter, not uncertainty of the interpolated background estimate. Input error/variance/DQ arrays are retained; uncertainty introduced by estimated background is not propagated, matching the NIRCam approach. Per-panel preview stretches differ.

Checks exact subtraction within float precision, unchanged error/variance/DQ arrays, unchanged sampled WCS and finite background. Large extended emission or detector structures may be included in the smooth background; this is not an artifact-removal algorithm. Review previews before further science use.

## Completed 2026-09-25

All 72 individual detector frames processed and validated. 72 full ASDFs, background FITS maps with RMS/mask extensions, receipts, and previews. WCS, DQ and existing uncertainties preserved.

{
  "background_median": [
    0.5509421229362488,
    0.6902140974998474
  ],
  "unmasked_median_after": [
    -0.0009992718696594238,
    0.0009202957153320312
  ],
  "masked_fraction": [
    0.06566669522941472,
    0.11234734088794084
  ],
  "frames": 72
}

Values remain DN/s: PHOTOM complete, FLUX incomplete. Background-estimate uncertainty is not propagated. No resampling.

Representative WFI07/WFI14 previews inspected: smooth structure is removed, but the WFI14 background model includes a localized feature near a bright extended source. Extended-source flux preservation has not been validated; the mask may need enlargement for that use. Preview axes are in the downsampled display grid (factor4), and each panel uses an independent stretch.


Future reduction order (user preference): run PHOTOM and then FluxStep immediately, before subsequent background subtractions. See FLUX.md. Current historical checkpoint order and DN/s products are preserved.
