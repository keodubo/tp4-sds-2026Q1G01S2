#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

REMOTE="${REMOTE:-origin}"
CURRENT_BRANCH="$(git branch --show-current || true)"
BRANCH="${BRANCH:-${CURRENT_BRANCH:-main}}"
RUN_TP4="${RUN_TP4:-1}"
RUN_TP3="${RUN_TP3:-1}"
USE_LFS="${USE_LFS:-1}"
COMMIT_MESSAGE="${COMMIT_MESSAGE:-data: add TP3 and TP4 simulation outputs}"
RUN_STAMP="${RUN_STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"

SYSTEM2_ROOT="outputs/system2-sweeps/system2-tp4-final"
TP3_ROOT="outputs/tp3-reference/tp3-final-grid"
SUMMARY_PATH="outputs/cloud-run-summary-${RUN_STAMP}.txt"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

ensure_clean_tracked_state() {
  git diff --quiet || fail "Tracked files have unstaged changes before the cloud run."
  git diff --cached --quiet || fail "The index has staged changes before the cloud run."

  local unexpected_untracked
  unexpected_untracked="$(git status --short --untracked-files=all | grep -vE '^\?\? outputs/' || true)"
  if [[ -n "${unexpected_untracked}" ]]; then
    echo "${unexpected_untracked}" >&2
    fail "Unexpected untracked files exist outside outputs/. Commit or remove them first."
  fi
}

ensure_lfs_ready() {
  if [[ "${USE_LFS}" != "1" ]]; then
    return
  fi
  git lfs version >/dev/null 2>&1 || fail "Git LFS is required. Install/enable git-lfs or rerun with USE_LFS=0 after checking file sizes."
  git lfs install --local >/dev/null
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

write_summary() {
  mkdir -p outputs
  {
    echo "run_stamp=${RUN_STAMP}"
    echo "git_head=$(git rev-parse HEAD)"
    echo "branch=${BRANCH}"
    echo "run_tp4=${RUN_TP4}"
    echo "run_tp3=${RUN_TP3}"
    echo
    echo "# Sizes"
    du -sh "${SYSTEM2_ROOT}" 2>/dev/null || true
    du -sh "${TP3_ROOT}" 2>/dev/null || true
    echo
    echo "# File counts"
    find "${SYSTEM2_ROOT}" -type f 2>/dev/null | wc -l | awk '{print "system2_files=" $1}'
    find "${TP3_ROOT}" -type f 2>/dev/null | wc -l | awk '{print "tp3_files=" $1}'
    echo
    echo "# Files over 95 MiB"
    find "${SYSTEM2_ROOT}" "${TP3_ROOT}" -type f -size +95M -print 2>/dev/null || true
  } >"${SUMMARY_PATH}"
  echo "Summary: ${SUMMARY_PATH}"
}

stage_outputs() {
  local roots_to_add=()
  if [[ "${RUN_TP4}" == "1" ]]; then
    roots_to_add+=("${SYSTEM2_ROOT}")
  fi
  if [[ "${RUN_TP3}" == "1" ]]; then
    roots_to_add+=("${TP3_ROOT}")
  fi
  roots_to_add+=("${SUMMARY_PATH}")

  if [[ "${USE_LFS}" != "1" ]]; then
    local oversized
    oversized="$(find "${roots_to_add[@]}" -type f -size +95M -print 2>/dev/null || true)"
    if [[ -n "${oversized}" ]]; then
      echo "${oversized}" >&2
      fail "Found files over 95 MiB and USE_LFS=0. Do not push these with normal Git."
    fi
  fi

  git add -f "${roots_to_add[@]}"
}

echo "Preparing cloud output run on ${BRANCH}."
ensure_clean_tracked_state
ensure_lfs_ready

git fetch "${REMOTE}" "${BRANCH}"
git merge --ff-only "${REMOTE}/${BRANCH}"

mkdir -p "${SYSTEM2_ROOT}" "${TP3_ROOT}"
run_and_log "script tests" "outputs/script-tests-${RUN_STAMP}.log" \
  python3 -m unittest discover -s scripts -p 'test_*.py'
git add -f "outputs/script-tests-${RUN_STAMP}.log"

if [[ "${RUN_TP4}" == "1" ]]; then
  run_and_log "TP4 System 2 full sweep" "${SYSTEM2_ROOT}/cloud-run-${RUN_STAMP}.log" \
    python3 scripts/run_system2_sweep.py --execute
fi

if [[ "${RUN_TP3}" == "1" ]]; then
  run_and_log "TP3 reference sweep" "${TP3_ROOT}/cloud-run-${RUN_STAMP}.log" \
    python3 scripts/run_tp3_reference_sweep.py --execute
fi

write_summary
stage_outputs

if git diff --cached --quiet; then
  echo "No output changes to commit."
  exit 0
fi

git status --short
git commit -m "${COMMIT_MESSAGE}"
git push "${REMOTE}" "HEAD:${BRANCH}"
echo "Pushed output commit to ${REMOTE}/${BRANCH}."
