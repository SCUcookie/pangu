#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/opt/pangu/pangu"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RUN_NAME="${RUN_NAME:-comparison_bundle_${TIMESTAMP}}"
RUN_DIR="${RUN_DIR:-${PROJECT_ROOT}/runtime/logs/${RUN_NAME}}"
LANGUAGE="${LANGUAGE:-zh}"
SPLIT="${SPLIT:-ablation}"
SYSTEMS_CSV="${SYSTEMS_CSV:-cascade_final,7b_only,current_v3}"
MAX_WORKERS="${MAX_WORKERS:-4}"
OUTPUT_TAG="${OUTPUT_TAG:-${RUN_NAME}}"
VLLM_API_URL_7B="${VLLM_API_URL_7B:-http://172.17.0.1:8000/v1/completions}"
MODEL_NAME_7B="${MODEL_NAME_7B:-pangu_embedded_7b}"
SAMPLE_FRACTION="${SAMPLE_FRACTION:-}"
SAMPLE_LIMIT="${SAMPLE_LIMIT:-}"

mkdir -p "${RUN_DIR}"

IFS=',' read -r -a SYSTEMS <<< "${SYSTEMS_CSV}"

MANIFEST="${RUN_DIR}/manifest.txt"
STATUS_TSV="${RUN_DIR}/status.tsv"

cat > "${MANIFEST}" <<EOF
run_name=${RUN_NAME}
run_dir=${RUN_DIR}
language=${LANGUAGE}
split=${SPLIT}
systems=${SYSTEMS_CSV}
max_workers=${MAX_WORKERS}
output_tag=${OUTPUT_TAG}
vllm_api_url_7b=${VLLM_API_URL_7B}
model_name_7b=${MODEL_NAME_7B}
sample_fraction=${SAMPLE_FRACTION}
sample_limit=${SAMPLE_LIMIT}
started_at=$(date -Is)
EOF

printf "system\tstatus\tlog_file\n" > "${STATUS_TSV}"

build_cmd() {
    local system="$1"
    local -a cmd=(
        python
        "${PROJECT_ROOT}/main_parallel.py"
        --system "${system}"
        --lang "${LANGUAGE}"
        --split "${SPLIT}"
        --max-workers "${MAX_WORKERS}"
        --output-tag "${OUTPUT_TAG}"
    )

    if [[ -n "${SAMPLE_FRACTION}" ]]; then
        cmd+=(--sample-fraction "${SAMPLE_FRACTION}")
    fi

    if [[ -n "${SAMPLE_LIMIT}" ]]; then
        cmd+=(--sample-limit "${SAMPLE_LIMIT}")
    fi

    printf '%q ' "${cmd[@]}"
}

for system in "${SYSTEMS[@]}"; do
    LOG_FILE="${RUN_DIR}/${system}.log"
    CMD_STRING="$(build_cmd "${system}")"

    {
        echo "[$(date -Is)] starting ${system}"
        echo "[$(date -Is)] command: ${CMD_STRING}"
    } > "${LOG_FILE}"

    if env \
        VLLM_API_URL_7B="${VLLM_API_URL_7B}" \
        MODEL_NAME_7B="${MODEL_NAME_7B}" \
        bash -lc "${CMD_STRING}" >> "${LOG_FILE}" 2>&1; then
        printf "%s\tcompleted\t%s\n" "${system}" "${LOG_FILE}" >> "${STATUS_TSV}"
    else
        printf "%s\tfailed\t%s\n" "${system}" "${LOG_FILE}" >> "${STATUS_TSV}"
        echo "[$(date -Is)] failed ${system}" >> "${LOG_FILE}"
        exit 1
    fi
done

echo "finished_at=$(date -Is)" >> "${MANIFEST}"
