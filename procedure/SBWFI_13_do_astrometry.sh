#!/usr/bin/env bash
set -euo pipefail
procedure_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Activate the roman environment before running this script.
source "$procedure_dir/roman_env.sh"
log_dir="$procedure_dir/../roman_tweakreg_test"
mkdir -p "$log_dir"
python -u "$procedure_dir/SBWFI_13_astrometry.py" "$@" 2>&1 | tee "$log_dir/tweakreg_$(date +%Y%m%dT%H%M%S).log"
