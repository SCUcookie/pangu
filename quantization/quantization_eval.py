from evalscope import run_task, TaskConfig

# 配置评测任务
task_cfg = TaskConfig(
    model='pangu_embedded_7b_w8a8',
    datasets=["mmlu_pro","cmmlu","ceval","piqa"],
    api_key='EMPTY',
    api_url='http://172.17.0.1:8001/v1',
    eval_type="openai_api",
    limit=10
)

# 启动评测
run_task(task_cfg)