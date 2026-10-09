#!/usr/bin/env bash
set -euo pipefail
procedure_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Activate a compatible environment before invoking; no machine-specific Conda path.
python_bin="${ROMAN_PYTHON:-python}"
export ROMAN_REDUCTION_ROOT="${ROMAN_REDUCTION_ROOT:-$(cd "$procedure_dir/.." && pwd)}"
export CRDS_PATH="${CRDS_PATH:-$ROMAN_REDUCTION_ROOT/crds_cache}"
export CRDS_SERVER_URL=https://roman-crds.stsci.edu
export CRDS_OBSERVATORY=roman
export CRDS_CONTEXT=roman_0072.pmap
export MPLCONFIGDIR="${MPLCONFIGDIR:-$ROMAN_REDUCTION_ROOT/.matplotlib}"
log_dir="$ROMAN_REDUCTION_ROOT/logs"
mkdir -p "$log_dir"
"$python_bin" -u "$procedure_dir/SBWFI_16_mosaic.py" "$@" 2>&1 | tee "$log_dir/mosaic_$(date +%Y%m%dT%H%M%S).log"
