"""
主程序 - AgentV3 (科研评估版)
华为盘古模型教育解题高级Agent - 动态认知路由与元认知评估
"""
import os
import json
import time
from datetime import datetime
from tqdm import tqdm
from typing import List, Dict, Any

from config import OUTPUT_DIR, DEBUG_MODE
from data_loader import DataLoader, DataItem
from inference_engine import InferenceEngine
from evaluator import GPT5Judge


class AgentV3:
    """教育解题Agent V3 - 核心创新：元认知反馈驱动的动态路由"""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.engine = InferenceEngine()
        self.judge = GPT5Judge()
        
        # 确保输出目录存在
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print("="*60)
        print("AgentV3 - Meta-Cognitive Dynamic Agent")
        print("="*60)
        print(f"调试模式: {'开启' if DEBUG_MODE else '关闭'}")
        print()
    
    def run(self, task_types: List[str] = None, sample_size: int = None, do_eval: bool = True):
        """
        运行Agent评估
        
        Args:
            task_types: 要处理的任务类型列表
            sample_size: 每种任务类型采样的数量 (用于快速调试)
            do_eval: 是否执行 GPT-5.4 评分评估
        """
        # 加载数据
        print("正在加载评估数据...")
        all_data = []
        if task_types:
            for t in task_types:
                data = self.data_loader.load_by_task(t)
                if sample_size and len(data) > sample_size:
                    data = data[:sample_size]
                all_data.extend(data)
        else:
            all_data = self.data_loader.load_all()
            if sample_size and len(all_data) > sample_size:
                all_data = all_data[:sample_size]
        
        if not all_data:
            print("⚠ 没有找到数据！")
            return
        
        print(f"已加载 {len(all_data)} 条评估数据\n")
        
        # 1. 动态路由推理
        results = []
        print("开始动态路由推理 (Fast -> Evaluate -> Slow)...")
        
        for item in tqdm(all_data, desc="推理进度"):
            result = self._process_item_v3(item)
            results.append(result)
        
        # 2. GPT-5.4 评分评估
        if do_eval:
            print("\n开始 GPT-5.4 专家评分评估 (Model-as-a-Judge)...")
            eval_results = []
            for res in tqdm(results, desc="评分进度"):
                # 获取评分
                scores = self.judge.judge_answer(
                    task_type=res["task_type"],
                    question=res["question"],
                    prediction=res["prediction"],
                    ground_truth=res["ground_truth"]
                )
                res["scores"] = scores
                eval_results.append(res)
            results = eval_results

        # 3. 保存结果
        self._save_results(results)
        
        # 4. 打印统计信息
        self._print_statistics(results)
    
    def _process_item_v3(self, item: DataItem) -> Dict[str, Any]:
        """使用AgentV3的动态路由逻辑处理单个数据项"""
        # 记录开始时间
        start_time = datetime.now()
        
        # 执行动态推理
        output = self.engine.infer_dynamic(item)
        
        # 记录耗时
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
        
        return result
    
    def _save_results(self, results: List[Dict[str, Any]]):
        """保存结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"proposed_v3_{timestamp}.jsonl")
        
        print(f"\n正在保存结果到: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        # 同时保存一份统计摘要
        summary_file = os.path.join(OUTPUT_DIR, f"summary_v3_{timestamp}.json")
        summary = self._generate_summary(results)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 详细结果与评估摘要已保存。")
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成AgentV3专属统计摘要"""
        total = len(results)
        slow_triggers = sum(1 for r in results if r["is_slow_triggered"])
        
        # 评分统计
        avg_score = 0
        metric_scores = {
            "IFTC": 0, "RTC": 0, "CRSC": 0,
            "BFA": 0, "DKA": 0, "RPR": 0,
            "CSI": 0, "MGP": 0, "HOTS": 0
        }
        count_with_scores = 0
        
        for r in results:
            if "scores" in r and "Average" in r["scores"]:
                avg_score += r["scores"]["Average"]
                count_with_scores += 1
                for m in metric_scores.keys():
                    metric_scores[m] += r["scores"].get(m, 0)
        
        if count_with_scores > 0:
            avg_score /= count_with_scores
            for m in metric_scores.keys():
                metric_scores[m] /= count_with_scores

        # 平均延迟
        avg_latency = sum(r["latency"] for r in results) / total if total > 0 else 0
        
        return {
            "total_items": total,
            "slow_trigger_rate": (slow_triggers / total) * 100 if total > 0 else 0,
            "average_latency": avg_latency,
            "overall_accuracy_avg": avg_score,
            "detailed_metrics": metric_scores,
            "timestamp": datetime.now().isoformat()
        }
    
    def _print_statistics(self, results: List[Dict[str, Any]]):
        """打印AgentV3评估统计信息"""
        summary = self._generate_summary(results)
        
        print("\n" + "="*60)
        print("AgentV3 最终评估报告")
        print("="*60)
        print(f"总计评估: {summary['total_items']} 条数据")
        print(f"平均准确率 (GPT-5.4 Judge): {summary['overall_accuracy_avg']:.2f}/10")
        print(f"慢思考触发率 (STR): {summary['slow_trigger_rate']:.2f}%")
        print(f"平均响应延迟: {summary['average_latency']:.2f}s")
        
        print(f"\n子维度平均分:")
        for m, score in summary['detailed_metrics'].items():
            print(f"  {m}: {score:.2f}")
        
        print("="*60)


def main():
    """评估运行主函数"""
    agent = AgentV3()
    
    # 运行全量评估 (sample_size=None)
    # 暂时关闭 GPT-5.4 评分评估 (do_eval=False) 以避免 404 错误并快速生成 Pangu 推理结果
    agent.run(sample_size=None, do_eval=False)


if __name__ == "__main__":
    main()
