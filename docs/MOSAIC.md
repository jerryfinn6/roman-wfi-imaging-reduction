# SBWFI_16 Roman mosaic preparation

Use `bash SBWFI_16_do_mosaic.sh` to prepare and validate the72-frame association and output WCS. Add `--run` to execute the full mosaic. Default input: SSD F106/stage2_flux; output: SSD F106/stage3_60mas. Override --input-dir/--output-dir as needed. Preparation does not drizzle or alter inputs.

Matches SBNRC_07 resampling choices: north-up rotation0degrees, pixel_scale0.06arcsec, square kernel, pixfrac1.0; inverse-variance weighting. Output shape, projection center and reference pixel are automatically derived from all72 input footprints. An automatic two-pixel border is added to avoid subpixel edge clipping from integer shape rounding. resample_on_skycell=False prevents a preset Roman skycell from overriding geometry. No hard-coded30000pixel footprint or external reference WCS. Checks all18detectors×4exposures, F106, photom/flatfield/tweakreg/flux COMPLETE, north orientation, scale and corner coverage. Saves association JSON, planned GWCS ASDF and preflight report.

Roman MosaicPipeline1.1.0 contains flux, skymatch, outlier_detection, resample, source_catalog. Flux skipped because all inputs already converted; skymatch skipped to retain current detector-specific background subtraction; source_catalog skipped as in SBNRC_07. Tweakreg is not a MosaicPipeline substep in this installed version. Outlier detection enabled with installed defaults (SNR5/4, derivative scale1.2/0.7); its intermediate grid uses pipeline defaults, while the final resample uses0.06arcsec north-up. Resample includes flat-field variance in propagated output errors. Existing background-estimation uncertainty remains unpropagated.

on_disk=True and in_memory=False limit input residency; scratch files for actual pipeline execution are placed under output. The full mosaic arrays and outlier-detection products can still require substantial RAM/disk; the preflight reports the size of a single float32 plane, not a total memory estimate. Current diffuse-source background caveat is retained. This script prepares a full focal-plane mosaic, including detector gaps, with no new mask tuning or background subtraction.

The actual output is a Roman coadd ASDF in MJy/sr. Surface brightness units remain MJy/sr at the new pixel scale; do not multiply science by an area ratio manually. No full mosaic has been run during code preparation. Association and WCS construction and configuration are tested; end-to-end outlier rejection/drizzle runtime remains to be tested.

RAM review: full in-memory estimate160–240GiB peak, not measured. Allow384–512GiB for headroom; disk-backed inputs alone do not remove large mosaic accumulator allocations. Full breakdown: workspace outputs/roman_mosaic_plan/RAM_ESTIMATE.md. Association grouping now explicitly sets four exposure groups of18detectors: simulator observation_id='?' otherwise combines all inputs into one group. Group construction verified without executing drizzle.


Portable runner update: activate the destination environment yourself; paths now resolve relative to procedure/. See TRANSFER_AND_RUN.md. Use --in-memory for memory-resident input/intermediate handling; default remains disk-backed.


Subset test: --detectors 1 2 3 4 5 selects20frames (four exposures per detector). Run with a distinct --product and --output-dir. Defaults still select all18detectors/72frames. Pipeline scratch cwd and tempfile directory both reside on the output volume. WFI01–05 preflight shape30082×20258; actual run started, validation pending.


Runtime diagnosis update: valid input timestamps exist (all four simulated exposures share the supplied timestamp). Roman1.1.0 ModelLibrary override does not propagate association group_id into model metadata; resampling sees the shared placeholder group across calls. Added ExposureGroupedLibrary to propagate explicit group IDs to borrowed working models. Verified distinct metadata group IDs for all four exposures with unchanged timestamps. Retry is running; end-to-end success is still pending. No input ASDFs or timestamps were rewritten.


## Validated subset run, 2026-09-25

20 frames, four exposure groups of five detectors. Outlier detection and resample COMPLETE. Saved coadd: SSD F106/stage3_WFI01_05_60mas/Roman_ISim_F106_WFI01_05_60mas_coadd.asdf (about9GB). Shape30082×20258, north-up, measured scale0.05999999997arcsec/pixel. 479930620 positive-weight pixels (78.754%coverage), all with finite science. Five covered pixels have nonfinite uncertainties; exclude them from uncertainty-based measurements. var_flat is entirely NaN because these inputs do not supply that component; errors combine available components and do not include background-estimation uncertainty. Variance reconstruction generated warnings; no silent repair was applied. Coadd flux status SKIPPED is expected: its inputs already had FluxStep COMPLETE and remain in MJy/sr.

Initial failure was corrected by propagating explicit association group IDs into working model metadata via ExposureGroupedLibrary. Input images/timestamps preserved. All simulation timestamps coincide; group assignments preserve the four distinct exposures. Actual20-frame runtime now passed; the full72-frame mosaic remains unexecuted. This confirms execution and basic product validity, not independent photometric/astrometric accuracy. Existing WFI14 background caveat remains relevant to the later full mosaic.

Inspected reduced-size science preview and generated weight preview; detector geometry/gaps visible. Detailed pixel counts in validation.json. Embedded calibration logs contain repeated copies of all frame messages; deduplicated by complete log line, not by numerical count.

Outlier flags: 20 per-frame messages, 3934–42307 pixels/frame, total 533627.
