"""
并行评估主程序 - 4实例并行推理
将数据均匀分成4份，分别发送到4个vLLM实例并行执行
"""
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from config import OUTPUT_DIR, DEBUG_MODE
from data_loader import DataLoader, DataItem
from inference_engine import InferenceEngine
from evaluator import GPT5Judge

# 4个vLLM实例的地址
VLLM_INSTANCES = [
    "http://172.17.0.1:8000/v1/completions",
    "http://172.17.0.1:8001/v1/completions",
    "http://172.17.0.1:8002/v1/completions",
    "http://172.17.0.1:8003/v1/completions",
]

VLLM_MODELS_URLS = [
    "http://172.17.0.1:8000/v1/models",
    "http://172.17.0.1:8001/v1/models",
    "http://172.17.0.1:8002/v1/models",
    "http://172.17.0.1:8003/v1/models",
]

progress_lock = Lock()
completed_count = 0
total_count = 0


def check_all_instances():
    """检查所有vLLM实例是否就绪"""
    import requests
    ready = []
    for i, url in enumerate(VLLM_MODELS_URLS):
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                print(f"  ✓ 实例 {i} (port {8000+i}) 就绪")
                ready.append(i)
            else:
                print(f"  ✗ 实例 {i} (port {8000+i}) 返回 {resp.status_code}")
        except Exception as e:
            print(f"  ✗ 实例 {i} (port {8000+i}) 不可用: {e}")
    return ready


def process_item(item: DataItem, engine: InferenceEngine) -> Dict[str, Any]:
    """使用指定引擎处理单个数据项"""
    global completed_count
    start_time = datetime.now()

    output = engine.infer_dynamic(item)

    duration = (datetime.now() - start_time).total_seconds()

    result = {
        "task_id": getattr(item, 'id', 'N/A'),
        "task_type": item.task_type,
        "question": item.question,
        "subject": item.subject,
        "education_level": item.education_level,
        "lang": item.lang,
        "prediction": output["final_answer"],
        "fast_response": output["fast_response"],
        "slow_thinking": output["slow_thinking"],
        "eval_label": output["eval_label"],
        "eval_reason": output["eval_reason"],
        "is_slow_triggered": output["is_slow_triggered"],
        "latency": duration,
        "ground_truth": item.answer
    }

    with progress_lock:
        completed_count += 1
        print(f"\r  进度: {completed_count}/{total_count} ({completed_count*100//total_count}%)", end="", flush=True)

    return result


def process_batch(items: List[DataItem], instance_idx: int) -> List[Dict[str, Any]]:
    """在指定实例上处理一批数据"""
    engine = InferenceEngine(
        api_url=VLLM_INSTANCES[instance_idx],
    )
    # 覆盖 models URL 检查 (构造函数已检查过)
    results = []
    for item in items:
        result = process_item(item, engine)
        result["instance_id"] = instance_idx
        results.append(result)
    return results


def save_results(results: List[Dict[str, Any]]):
    """保存结果"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"parallel_4x2_{timestamp}.jsonl")

    print(f"\n正在保存结果到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    # 统计摘要
    total = len(results)
    slow_triggers = sum(1 for r in results if r["is_slow_triggered"])
    avg_latency = sum(r["latency"] for r in results) / total if total > 0 else 0

    summary = {
        "total_items": total,
        "slow_trigger_rate": (slow_triggers / total) * 100 if total > 0 else 0,
        "average_latency_per_item": avg_latency,
        "num_instances": 4,
        "timestamp": datetime.now().isoformat()
    }

    summary_file = os.path.join(OUTPUT_DIR, f"summary_parallel_4x2_{timestamp}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"✓ 结果已保存。")
    return summary


def main():
    global total_count, completed_count

    print("=" * 60)
    print("AgentV3 - 4×2 并行评估模式")
    print("4个vLLM实例 × 2张NPU卡")
    print("=" * 60)

    # 1. 检查实例
    print("\n检查vLLM实例状态...")
    ready = check_all_instances()
    if not ready:
        print("\n⚠ 没有可用的vLLM实例！请先运行 run_service_7b_4x2.sh")
        return
    print(f"\n可用实例: {len(ready)}/4")

    # 2. 加载数据
    print("\n正在加载评估数据...")
    loader = DataLoader()
    all_data = loader.load_all()

    if not all_data:
        print("⚠ 没有找到数据！")
        return
    print(f"已加载 {len(all_data)} 条数据")

    # 3. 均匀分割数据到可用实例
    num_instances = len(ready)
    batches = [[] for _ in range(num_instances)]
    for i, item in enumerate(all_data):
        batches[i % num_instances].append(item)

    for i, batch in enumerate(batches):
        print(f"  实例 {ready[i]}: {len(batch)} 条数据")

    # 4. 并行推理
    total_count = len(all_data)
    completed_count = 0
    all_results = []

    print(f"\n开始 {num_instances} 路并行推理...")
    wall_start = time.time()

    with ThreadPoolExecutor(max_workers=num_instances) as executor:
        futures = {}
        for i, batch in enumerate(batches):
            future = executor.submit(process_batch, batch, ready[i])
            futures[future] = ready[i]

        for future in as_completed(futures):
            instance_id = futures[future]
            try:
                batch_results = future.result()
                all_results.extend(batch_results)
            except Exception as e:
                print(f"\n⚠ 实例 {instance_id} 出错: {e}")

    wall_time = time.time() - wall_start

    # 按原始顺序排序（可选）
    print(f"\n\n并行推理完成！")

    # 5. 保存并打印统计
    summary = save_results(all_results)

    print("\n" + "=" * 60)
    print("并行评估报告")
    print("=" * 60)
    print(f"总计评估: {summary['total_items']} 条数据")
    print(f"使用实例: {num_instances} 个")
    print(f"慢思考触发率: {summary['slow_trigger_rate']:.2f}%")
    print(f"平均单条延迟: {summary['average_latency_per_item']:.2f}s")
    print(f"总挂钟时间: {wall_time:.2f}s")
    print(f"吞吐量: {summary['total_items'] / wall_time:.2f} items/s")

    if summary['total_items'] > 0:
        estimated_single = summary['average_latency_per_item'] * summary['total_items']
        speedup = estimated_single / wall_time if wall_time > 0 else 0
        print(f"预估加速比: {speedup:.2f}x (vs 单实例串行)")
    print("=" * 60)


if __name__ == "__main__":
    main()
