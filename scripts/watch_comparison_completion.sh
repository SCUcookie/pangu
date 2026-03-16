#!/bin/bash
set -euo pipefail

RUN_DIR="${RUN_DIR:?RUN_DIR is required}"
POLL_SECONDS="${POLL_SECONDS:-20}"
SESSION_NAME="${SESSION_NAME:-}"

STATUS_TSV="${RUN_DIR}/status.tsv"
MANIFEST="${RUN_DIR}/manifest.txt"
DONE_FILE="${RUN_DIR}/DONE.txt"
PROMPT_FILE="${RUN_DIR}/NEXT_PROMPT.txt"
BUNDLE_LOG="${RUN_DIR}/bundle.log"

read_manifest_value() {
    local key="$1"
    if [[ ! -f "${MANIFEST}" ]]; then
        return 1
    fi
    awk -F= -v k="${key}" '$1 == k {print substr($0, index($0, "=") + 1)}' "${MANIFEST}" | tail -n 1
}

SYSTEMS_CSV="$(read_manifest_value systems || true)"
RUN_NAME="$(read_manifest_value run_name || true)"
OUTPUT_TAG="$(read_manifest_value output_tag || true)"
LANGUAGE="$(read_manifest_value language || true)"
SPLIT="$(read_manifest_value split || true)"

IFS=',' read -r -a SYSTEMS <<< "${SYSTEMS_CSV}"
EXPECTED_COUNT="${#SYSTEMS[@]}"

while true; do
    COMPLETED_COUNT=0
    FAILED_COUNT=0

    if [[ -f "${STATUS_TSV}" ]]; then
        COMPLETED_COUNT="$(awk -F'\t' 'NR > 1 && $2 == "completed" {count++} END {print count + 0}' "${STATUS_TSV}")"
        FAILED_COUNT="$(awk -F'\t' 'NR > 1 && $2 == "failed" {count++} END {print count + 0}' "${STATUS_TSV}")"
    fi

    if [[ $((COMPLETED_COUNT + FAILED_COUNT)) -ge "${EXPECTED_COUNT}" ]]; then
        break
    fi

    if [[ -n "${SESSION_NAME}" ]] && command -v screen >/dev/null 2>&1; then
        if ! screen -ls | grep -q "[.]${SESSION_NAME}[[:space:]]"; then
            if [[ $((COMPLETED_COUNT + FAILED_COUNT)) -gt 0 ]]; then
                break
            fi
        fi
    fi

    sleep "${POLL_SECONDS}"
done

{
    echo "Comparison bundle finished at $(date -Is)."
    echo "Run name: ${RUN_NAME}"
    echo "Run directory: ${RUN_DIR}"
    echo "Language: ${LANGUAGE}"
    echo "Split: ${SPLIT}"
    echo
    echo "Status table:"
    cat "${STATUS_TSV}"
    echo
    echo "Summary files:"
    if [[ -n "${OUTPUT_TAG}" ]]; then
        find /opt/pangu/pangu/outputs/summaries -maxdepth 1 -type f | grep "${OUTPUT_TAG}" | sort || true
    fi
} > "${DONE_FILE}"

{
    echo "The comparison run ${RUN_NAME} is finished."
    echo
    echo "Use this prompt:"
    echo
    echo "Read ${RUN_DIR}/status.tsv and all summary JSON files matching output tag ${OUTPUT_TAG} under /opt/pangu/pangu/outputs/summaries, then summarize the results and tell me which tables/figures in the paper should be updated."
} > "${PROMPT_FILE}"

{
    echo
    echo "[$(date -Is)] comparison watcher: run finished"
    echo "[$(date -Is)] done file: ${DONE_FILE}"
    echo "[$(date -Is)] next prompt: ${PROMPT_FILE}"
} >> "${BUNDLE_LOG}"
