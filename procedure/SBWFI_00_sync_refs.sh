#!/usr/bin/env bash
set -euo pipefail
procedure_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$procedure_dir/roman_env.sh"
if [[ "${CONDA_DEFAULT_ENV:-}" != roman && "${CONDA_PREFIX:-}" != */envs/roman ]]; then
    echo 'Activate the roman Conda environment first.' >&2; exit 1
fi
root="${1:-/path/to/Roman_I-Sim_reduction}"
shopt -s nullglob
files=("$root"/F[0-9][0-9][0-9]/stage1/*_uncal.asdf)
if (( ${#files[@]} == 0 )); then
    echo 'No sorted uncalibrated files found. Run the sorter first.' >&2; exit 1
fi
mkdir -p "$root/logs" "$CRDS_PATH"
log="$root/logs/crds_sync_$(date -u +%Y%m%dT%H%M%SZ).log"
printf 'Context: %s\nCache: %s\nDatasets: %s\n' "$CRDS_CONTEXT" "$CRDS_PATH" "${#files[@]}" | tee "$log"
crds sync --roman --contexts "$CRDS_CONTEXT" --fetch-references \
    --dataset-files "${files[@]}" 2>&1 | tee -a "$log"
