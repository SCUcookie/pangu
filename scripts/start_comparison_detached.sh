#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/opt/pangu/pangu"
LOG_ROOT="${PROJECT_ROOT}/runtime/logs"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RUN_NAME="${RUN_NAME:-comparison_detached_${TIMESTAMP}}"
RUN_DIR="${RUN_DIR:-${LOG_ROOT}/${RUN_NAME}}"
SESSION_NAME="${SESSION_NAME:-${RUN_NAME}}"
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
ln -sfn "${RUN_DIR}" "${LOG_ROOT}/comparison_latest"

BUNDLE_LOG="${RUN_DIR}/bundle.log"
PID_FILE="${RUN_DIR}/bundle.pid"
SESSION_FILE="${RUN_DIR}/screen.session"
WATCHER_LOG="${RUN_DIR}/watcher.log"
WATCHER_SESSION_NAME="${SESSION_NAME}_watch"
PROMPT_FILE="${RUN_DIR}/NEXT_PROMPT.txt"
DONE_FILE="${RUN_DIR}/DONE.txt"

if command -v screen >/dev/null 2>&1; then
    SCREEN_CMD="env RUN_NAME='${RUN_NAME}' RUN_DIR='${RUN_DIR}' LANGUAGE='${LANGUAGE}' SPLIT='${SPLIT}' SYSTEMS_CSV='${SYSTEMS_CSV}' MAX_WORKERS='${MAX_WORKERS}' OUTPUT_TAG='${OUTPUT_TAG}' VLLM_API_URL_7B='${VLLM_API_URL_7B}' MODEL_NAME_7B='${MODEL_NAME_7B}' SAMPLE_FRACTION='${SAMPLE_FRACTION}' SAMPLE_LIMIT='${SAMPLE_LIMIT}' bash '${PROJECT_ROOT}/scripts/run_comparison_bundle.sh' > '${BUNDLE_LOG}' 2>&1"
    screen -dmS "${SESSION_NAME}" bash -lc "${SCREEN_CMD}"
    WATCHER_CMD="env RUN_DIR='${RUN_DIR}' SESSION_NAME='${SESSION_NAME}' bash '${PROJECT_ROOT}/scripts/watch_comparison_completion.sh' > '${WATCHER_LOG}' 2>&1"
    screen -dmS "${WATCHER_SESSION_NAME}" bash -lc "${WATCHER_CMD}"
    echo "${SESSION_NAME}" > "${SESSION_FILE}"
    : > "${PID_FILE}"
else
    nohup env \
        RUN_NAME="${RUN_NAME}" \
        RUN_DIR="${RUN_DIR}" \
        LANGUAGE="${LANGUAGE}" \
        SPLIT="${SPLIT}" \
        SYSTEMS_CSV="${SYSTEMS_CSV}" \
        MAX_WORKERS="${MAX_WORKERS}" \
        OUTPUT_TAG="${OUTPUT_TAG}" \
        VLLM_API_URL_7B="${VLLM_API_URL_7B}" \
        MODEL_NAME_7B="${MODEL_NAME_7B}" \
        SAMPLE_FRACTION="${SAMPLE_FRACTION}" \
        SAMPLE_LIMIT="${SAMPLE_LIMIT}" \
        bash "${PROJECT_ROOT}/scripts/run_comparison_bundle.sh" > "${BUNDLE_LOG}" 2>&1 < /dev/null &

    CHILD_PID=$!
    disown "${CHILD_PID}" 2>/dev/null || true
    echo "${CHILD_PID}" > "${PID_FILE}"
fi

cat > "${RUN_DIR}/README.txt" <<EOF
Run name: ${RUN_NAME}
Run directory: ${RUN_DIR}
Bundle log: ${BUNDLE_LOG}
PID file: ${PID_FILE}
Screen session file: ${SESSION_FILE}
Done file: ${DONE_FILE}
Prompt file: ${PROMPT_FILE}
Language: ${LANGUAGE}
Split: ${SPLIT}
Systems: ${SYSTEMS_CSV}
Max workers: ${MAX_WORKERS}
Output tag: ${OUTPUT_TAG}
7B endpoint: ${VLLM_API_URL_7B}
Sample fraction: ${SAMPLE_FRACTION}
Sample limit: ${SAMPLE_LIMIT}

Status files:
- ${RUN_DIR}/manifest.txt
- ${RUN_DIR}/status.tsv

Useful commands:
tail -f ${BUNDLE_LOG}
tail -f ${WATCHER_LOG}
cat ${RUN_DIR}/status.tsv
screen -ls | rg ${SESSION_NAME}
EOF

echo "Run name: ${RUN_NAME}"
echo "Run directory: ${RUN_DIR}"
if [[ -s "${SESSION_FILE}" ]]; then
    echo "Screen session: $(cat "${SESSION_FILE}")"
else
    echo "Bundle pid: $(cat "${PID_FILE}")"
fi
