# Step 17: Roman ASDF to FITS

Use `SBWFI_17_asdf_to_fits.py` in the roman environment:

```sh
python SBWFI_17_asdf_to_fits.py /path/product_coadd.asdf --output-dir /path/fits
```

Accepts multiple 2D calibrated image or mosaic ASDF inputs. Exports available science, error, weight, variance, DQ and context arrays into separate primary-HDU FITS files. It refuses existing outputs. Raw multi-resultant ramps require a separate plane-selection procedure.

The celestial GWCS is approximated with FITS SIP and independently checked on a 43 by 41 grid, with a default maximum error of 0.01 pixel. No pixel subtraction or image shift is applied. The original ASDF remains the authoritative full metadata/GWCS product. Checksums and exact pixel equality, including NaNs, are checked after writing. FITS can be opened in DS9; start with the `_sci.fits` file.

Unit inference follows this calibrated workflow: completed flux or resample means MJy/sr; otherwise DN/s. Before applying to unrelated products, verify their units and calibration history; resampling alone does not establish physical units. Variances have squared science units. Weight units are intentionally unspecified; context and DQ retain integer bit fields. No flux conversion occurs during extraction.

## WFI01–05 mosaic export, 2026-09-25

Seven FITS files are in SSD `F106/stage3_WFI01_05_60mas/fits/`: sci, err, wht, var_poisson, var_rnoise, var_flat and context. Each is approximately 2.44 GB; total approximately 17.06 GB. Science shape is 30082 by 20258, north-up at 0.06 arcsec/pixel, MJy/sr. Maximum tested WCS discrepancy: 0.000015632 pixel. All seven files passed pixel equality and checksum validation.

Existing limitations are preserved: five covered pixels have invalid uncertainties, flat variance is unavailable (all NaN), and background-estimate uncertainty was not propagated. This is an export of the completed subset mosaic, not a new calibration or an export of all 72 individual detector images.

After step 16 finishes, export the full 18-detector mosaic from the reduction root:

```bash
python procedure/SBWFI_17_asdf_to_fits.py \
  F106/stage3_60mas/Roman_ISim_F106_60mas_northup_coadd.asdf \
  --output-dir F106/stage3_60mas/fits
```

Step 17 uses the validated extractor unchanged. The former optional script name remains a compatibility entry point. Existing exports need not be rerun.
