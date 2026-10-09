# Source detection for astrometry review

SBWFI_12_source_catalog.py uses Roman SourceCatalogStep, with Photutils segmentation.
Settings mapped from SBNRC_04_AstroSex.py and sex.sex:
4-sigma detection, 5 connected pixels, 2-pixel Gaussian FWHM, background mesh 128,
deblending enabled (pipeline contrast 1e-4). PSF fitting is disabled to use
windowed centroids analogous to XWIN/YWIN. No subtraction of 1 is applied.

Differences: pipeline detection uses a background RMS image rather than the
SExtractor MAP_RMS input; its Gaussian footprint/background smoothing need not
match SExtractor exactly. All invalid science/error pixels, nonpositive errors
and DO_NOT_USE pixels are masked by the pipeline. No source threshold tuning or
astrometric fit is hidden in this procedure.

Alignment candidates require finite windowed centroids, a symmetric 10-pixel
border, segmentation footprint >=10 actual pixels, positive segment flux/error,
and 1.085736*segment_flux_err/segment_flux <=0.2. Segmentation area is counted
from the label map; pipeline segment_area is a sky area, not a pixel count.
Candidate centroids on invalid or DO_NOT_USE pixels are also excluded.
This is a candidate list, not a validated stellar reference sample: edge features
and detector artifacts may still pass these cuts. Review red-circle overlays
before applying tweakreg. The full catalog is retained for later tuning.

SSD outputs:
- F106/source_catalog/*_cat.parquet — native full pipeline catalogs
- F106/source_catalog/*_segm.asdf — segmentation and detection images
- F106/source_catalog/*_all.ecsv — full table for inspection
- F106/source_catalog/*_phot.ecsv — selected zero-based alignment candidates
- F106/source_catalog/*_detection.json — counts and parameters

Preview files: workspace outputs/roman_source_previews while running; a copy will
be placed in SSD F106/source_catalog_imshow upon completion. Each frame has
_all.png and _selected.png, with red circles, gray_r, ZScale and origin lower.
Final index.html links both versions. Original calibrated images are not modified.

## Completed 2026-09-25

All 72 frames processed. Verified 72 native catalogs, 72 segmentation maps, 72 full ECSV tables, 72 selected catalogs and 144 valid PNGs. Selected centroid coordinates match the pipeline windowed centroids directly with no origin shift. All selected coordinates satisfy the specified border.

Detected counts range from 1,818 to 45,189; selected candidates from 1,495 to 9,452. WFI07 has about 45,000 detections in each exposure and WFI14 about 17,000. These large detector-dependent counts and the overlays indicate substantial artifact contamination; do not pass these lists directly into an astrometric fit without further quality selection/masking. Brightness/area cuts alone are insufficient. No tweakreg has been run.

All/selected preview gallery and ZIP are in the workspace outputs; previews are also copied to SSD F106/source_catalog_imshow. Heartbeat paused after completion.
