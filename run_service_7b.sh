export ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
export VLLM_USE_V1=1

HOST=0.0.0.0
PORT=8000


LOCAL_CKPT_DIR=/opt/pangu/openPangu-Embedded-7B-V1.1

SERVED_MODEL_NAME=pangu_embedded_7b


vllm serve $LOCAL_CKPT_DIR \
    --served-model-name $SERVED_MODEL_NAME \
    --tensor-parallel-size 4 \
    --trust-remote-code \
    --host $HOST \
    --port $PORT \
    --max-num-seqs 32 \
    --max-model-len 16384 \
    --max-num-batched-tokens 4096 \
    --tokenizer-mode "slow" \
    --dtype bfloat16 \
    --distributed-executor-backend mp \
    --gpu-memory-utilization 0.90 \
    --no-enable-prefix-caching \
    --no-enable-chunked-prefill
