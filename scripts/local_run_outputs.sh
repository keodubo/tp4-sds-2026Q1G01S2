#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

RUN_TP4="${RUN_TP4:-1}"
RUN_TP3="${RUN_TP3:-1}"
PRECHECK_ONLY="${PRECHECK_ONLY:-0}"
PACKAGE_OUTPUTS="${PACKAGE_OUTPUTS:-1}"
RESUME="${RESUME:-0}"
RUN_STAMP="${RUN_STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
PART_SIZE="${PART_SIZE:-1900m}"

SYSTEM2_ROOT="outputs/system2-sweeps/system2-tp4-final"
TP3_ROOT="outputs/tp3-reference/tp3-final-grid"
ARCHIVE_ROOT="outputs/local-archives/${RUN_STAMP}"
SUMMARY_PATH="outputs/local-run-summary-${RUN_STAMP}.txt"
SCRIPT_TEST_LOG="outputs/local-script-tests-${RUN_STAMP}.log"
CHECKSUM_PATH="${ARCHIVE_ROOT}/SHA256SUMS.txt"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

run_and_log() {
  local label="$1"
  local log_path="$2"
  shift 2
  mkdir -p "$(dirname "${log_path}")"
  {
    echo "# ${label}"
    echo "started_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "command=$*"
    "$@"
    echo "finished_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } >"${log_path}" 2>&1
  echo "${label} log: ${log_path}"
}

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1"
  else
    shasum -a 256 "$1"
  fi
}

count_files() {
  local label="$1"
  local path="$2"
  if [[ -d "${path}" ]]; then
    find "${path}" -type f | wc -l | awk -v label="${label}" '{print label "=" $1}'
  else
    echo "${label}=0"
  fi
}

archive_tree() {
  local label="$1"
  local source_path="$2"
  local output_prefix="${ARCHIVE_ROOT}/${label}.tar.gz.part-"

  if [[ ! -d "${source_path}" ]]; then
    echo "Skipping missing ${source_path}"
    return
  fi

  mkdir -p "${ARCHIVE_ROOT}"
  echo "Archiving ${source_path} into ${ARCHIVE_ROOT} with part size ${PART_SIZE}."
  tar -czf - "${source_path}" | split -b "${PART_SIZE}" - "${output_prefix}"
}

write_summary() {
  mkdir -p outputs
  {
    echo "run_stamp=${RUN_STAMP}"
    echo "git_head=$(git rev-parse HEAD)"
    echo "run_tp4=${RUN_TP4}"
    echo "run_tp3=${RUN_TP3}"
    echo "resume=${RESUME}"
    echo "precheck_only=${PRECHECK_ONLY}"
    echo "package_outputs=${PACKAGE_OUTPUTS}"
    echo
    echo "# Sizes"
    du -sh "${SYSTEM2_ROOT}" 2>/dev/null || true
    du -sh "${TP3_ROOT}" 2>/dev/null || true
    du -sh "${ARCHIVE_ROOT}" 2>/dev/null || true
    echo
    echo "# File counts"
    count_files "system2_files" "${SYSTEM2_ROOT}"
    count_files "tp3_files" "${TP3_ROOT}"
    count_files "archive_files" "${ARCHIVE_ROOT}"
    echo
    echo "# Logs"
    echo "script_tests=${SCRIPT_TEST_LOG}"
    if [[ "${RUN_TP4}" == "1" ]]; then
      echo "tp4=${SYSTEM2_ROOT}/local-run-${RUN_STAMP}.log"
    fi
    if [[ "${RUN_TP3}" == "1" ]]; then
      echo "tp3=${TP3_ROOT}/local-run-${RUN_STAMP}.log"
    fi
  } >"${SUMMARY_PATH}"
  echo "Summary: ${SUMMARY_PATH}"
}

package_outputs() {
  if [[ "${PACKAGE_OUTPUTS}" != "1" ]]; then
    return
  fi

  rm -rf "${ARCHIVE_ROOT}"
  mkdir -p "${ARCHIVE_ROOT}"

  if [[ "${RUN_TP4}" == "1" ]]; then
    archive_tree "system2-tp4-final" "${SYSTEM2_ROOT}"
  fi
  if [[ "${RUN_TP3}" == "1" ]]; then
    archive_tree "tp3-final-grid" "${TP3_ROOT}"
  fi

  : >"${CHECKSUM_PATH}"
  find "${ARCHIVE_ROOT}" -type f ! -name "SHA256SUMS.txt" -print0 \
    | sort -z \
    | while IFS= read -r -d '' asset; do
        hash_file "${asset}" >>"${CHECKSUM_PATH}"
      done
}

if [[ "${RUN_TP4}" != "1" && "${RUN_TP3}" != "1" ]]; then
  fail "At least one of RUN_TP4 or RUN_TP3 must be 1."
fi

echo "Starting local output run ${RUN_STAMP}."
echo "RUN_TP4=${RUN_TP4} RUN_TP3=${RUN_TP3} RESUME=${RESUME} PRECHECK_ONLY=${PRECHECK_ONLY} PACKAGE_OUTPUTS=${PACKAGE_OUTPUTS}"

mkdir -p "${SYSTEM2_ROOT}" "${TP3_ROOT}"
run_and_log "script tests" "${SCRIPT_TEST_LOG}" \
  python3 -m unittest discover -s scripts -p 'test_*.py'

if [[ "${PRECHECK_ONLY}" == "1" ]]; then
  if [[ "${RUN_TP4}" == "1" ]]; then
    run_and_log "TP4 System 2 dry run" "${SYSTEM2_ROOT}/local-dry-run-${RUN_STAMP}.log" \
      python3 scripts/run_system2_sweep.py
  fi
  if [[ "${RUN_TP3}" == "1" ]]; then
    run_and_log "TP3 reference dry run" "${TP3_ROOT}/local-dry-run-${RUN_STAMP}.log" \
      python3 scripts/run_tp3_reference_sweep.py
  fi
  write_summary
  echo "Local precheck finished. No heavy simulations were executed."
  exit 0
fi

if [[ "${RUN_TP4}" == "1" ]]; then
  system2_args=(scripts/run_system2_sweep.py --execute)
  if [[ "${RESUME}" == "1" ]]; then
    system2_args+=(--resume)
  fi
  run_and_log "TP4 System 2 full sweep" "${SYSTEM2_ROOT}/local-run-${RUN_STAMP}.log" \
    python3 "${system2_args[@]}"
fi

if [[ "${RUN_TP3}" == "1" ]]; then
  tp3_args=(scripts/run_tp3_reference_sweep.py --execute)
  if [[ "${RESUME}" == "1" ]]; then
    tp3_args+=(--resume)
  fi
  run_and_log "TP3 reference sweep" "${TP3_ROOT}/local-run-${RUN_STAMP}.log" \
    python3 "${tp3_args[@]}"
fi

package_outputs
write_summary
echo "Local output run finished."
