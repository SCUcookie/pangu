#!/bin/bash
# 启动4个vLLM实例，每个使用2张NPU卡
# 实例0: NPU 0,1 -> 端口 8000
# 实例1: NPU 2,3 -> 端口 8001
# 实例2: NPU 4,5 -> 端口 8002
# 实例3: NPU 6,7 -> 端口 8003

export VLLM_USE_V1=1

LOCAL_CKPT_DIR=/opt/pangu/openPangu-Embedded-7B-V1.1
SERVED_MODEL_NAME=pangu_embedded_7b
HOST=0.0.0.0

DEVICES=("0,1" "2,3" "4,5" "6,7")
PORTS=(8000 8001 8002 8003)

for i in 0 1 2 3; do
    echo "=========================================="
    echo "Starting instance $i on NPU ${DEVICES[$i]}, port ${PORTS[$i]}"
    echo "=========================================="

    ASCEND_RT_VISIBLE_DEVICES=${DEVICES[$i]} vllm serve $LOCAL_CKPT_DIR \
        --served-model-name $SERVED_MODEL_NAME \
        --tensor-parallel-size 2 \
        --trust-remote-code \
        --host $HOST \
        --port ${PORTS[$i]} \
        --max-num-seqs 16 \
        --max-model-len 16384 \
        --max-num-batched-tokens 4096 \
        --tokenizer-mode "slow" \
        --dtype bfloat16 \
        --distributed-executor-backend mp \
        --gpu-memory-utilization 0.90 \
        --no-enable-prefix-caching \
        --no-enable-chunked-prefill &

    echo "Instance $i started with PID $!"
done

echo ""
echo "=========================================="
echo "All 4 instances launched!"
echo "Ports: 8000, 8001, 8002, 8003"
echo "Use 'kill %1 %2 %3 %4' or 'pkill -f vllm' to stop all"
echo "=========================================="

wait
