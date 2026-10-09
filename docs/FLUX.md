# Flux conversion and future processing order

User preference: for future reductions run PHOTOM then FluxStep immediately, as a paired operation, before subsequent subtraction steps. PHOTOM loads calibration metadata; FluxStep scales data and error by conversion_megajanskys and variance arrays by its square. Record and verify flux=COMPLETE to avoid double conversion. Units after FluxStep are MJy/sr, a surface brightness, not integrated source flux.

For this existing reduction only: SBWFI_15_flux.py converts the completed background-subtracted DN/s images into separate products in outputs/roman_flux. It verifies data/error/variance scaling and unchanged WCS/DQ. The original DN/s products remain available. Scripts and historical checkpoint order are retained to preserve restart compatibility. For a future run, call this script with --input-dir pointing to the PHOTOM outputs and --pattern 'r*_photom.asdf', before proceeding; adapt subsequent input paths to those flux products. The existing roman_staged historical checkpoint runner does not automatically insert this new step.

For scalar conversion C and the same estimated background B, C*(D-B)=C*D-C*B apart from floating point rounding. Moving unit conversion cannot fix any real source light mistakenly included in B. Background-estimate uncertainty remains unpropagated. Future background maps and thresholds must use their input units consistently; do not label flux-input backgrounds DN/s.

All72 converted and validated, with COMPLETE flux status. SSD stage2_flux copies verified by count/size.
