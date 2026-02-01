"""
主程序 - AgentV2
华为盘古模型教育解题高级Agent
"""
import os
import json
from datetime import datetime
from tqdm import tqdm
from typing import List, Dict, Any

from config import OUTPUT_DIR, DEBUG_MODE
from data_loader import DataLoader, DataItem
from difficulty_decision import DifficultyDecision
from inference_engine import InferenceEngine


class AgentV2:
    """教育解题Agent V2 - 支持快慢思考"""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.decider = DifficultyDecision()
        self.engine = InferenceEngine()
        
        # 确保输出目录存在
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print("="*60)
        print("AgentV2")
        print("="*60)
        print(f"调试模式: {'开启' if DEBUG_MODE else '关闭'}")
        print()
    
    def run(self, task_types: List[str] = None):
        """
        运行Agent
        
        Args:
            task_types: 要处理的任务类型列表，None表示处理所有任务
        """
        # 加载数据
        print("正在加载数据...")
        if task_types:
            all_data = []
            for task_type in task_types:
                all_data.extend(self.data_loader.load_by_task(task_type))
        else:
            all_data = self.data_loader.load_all()
        
        if not all_data:
            print("⚠ 没有找到数据！")
            return
        
        print(f"已加载 {len(all_data)} 条数据\n")
        
        # 处理每个数据项
        results = []
        print("开始推理...")
        
        for item in tqdm(all_data, desc="推理进度"):
            result = self._process_item(item)
            results.append(result)
        
        # 保存结果
        self._save_results(results)
        
        # 打印统计信息
        self._print_statistics(results)
    
    def _process_item(self, item: DataItem) -> Dict[str, Any]:
        """处理单个数据项"""
        # 决策：快思考 vs 慢思考
        decision = self.decider.decide(item)
        
        # 执行推理
        if decision == "fast":
            prediction = self.engine.infer_fast(item)
            result = {
                "task_type": item.task_type,
                "question": item.question,
                "prompt": item.prompt,
                "subject": item.subject,
                "education_level": item.education_level,
                "question_type": item.question_type,
                "lang": item.lang,
                "source_file": item.source_file,
                "decision": decision,
                "prediction_fast": prediction,
                "ground_truth": item.answer
            }
        
        elif decision == "slow":
            prediction = self.engine.infer_slow(item)
            result = {
                "task_type": item.task_type,
                "question": item.question,
                "prompt": item.prompt,
                "subject": item.subject,
                "education_level": item.education_level,
                "question_type": item.question_type,
                "lang": item.lang,
                "source_file": item.source_file,
                "decision": decision,
                "prediction_slow": prediction,
                "ground_truth": item.answer
            }
        
        else:  # both
            # 先慢后快
            predictions = self.engine.infer_slow_then_fast(item)
            result = {
                "task_type": item.task_type,
                "question": item.question,
                "prompt": item.prompt,
                "subject": item.subject,
                "education_level": item.education_level,
                "question_type": item.question_type,
                "lang": item.lang,
                "source_file": item.source_file,
                "decision": decision,
                "prediction_slow": predictions["slow_thinking"],
                "prediction_fast": predictions["fast_answer"],
                "ground_truth": item.answer
            }
        
        return result
    
    def _save_results(self, results: List[Dict[str, Any]]):
        """保存结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"predictions_{timestamp}.jsonl")
        
        print(f"\n正在保存结果到: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        print(f"✓ 结果已保存")
        
        # 同时保存一份统计摘要
        summary_file = os.path.join(OUTPUT_DIR, f"summary_{timestamp}.json")
        summary = self._generate_summary(results)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 统计摘要已保存到: {summary_file}")
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成统计摘要"""
        # 统计决策分布
        decision_counts = {"fast": 0, "slow": 0, "both": 0}
        task_counts = {}
        lang_counts = {"zh": 0, "en": 0}
        
        for result in results:
            decision_counts[result["decision"]] += 1
            task_type = result["task_type"]
            task_counts[task_type] = task_counts.get(task_type, 0) + 1
            lang_counts[result["lang"]] += 1
        
        return {
            "total_items": len(results),
            "decision_distribution": decision_counts,
            "task_distribution": task_counts,
            "language_distribution": lang_counts,
            "timestamp": datetime.now().isoformat()
        }
    
    def _print_statistics(self, results: List[Dict[str, Any]]):
        """打印统计信息"""
        summary = self._generate_summary(results)
        
        print("\n" + "="*60)
        print("统计信息")
        print("="*60)
        print(f"总计处理: {summary['total_items']} 条数据")
        print(f"\n决策分布:")
        for decision, count in summary['decision_distribution'].items():
            percentage = (count / summary['total_items']) * 100
            print(f"  {decision}: {count} ({percentage:.1f}%)")
        
        print(f"\n任务类型分布:")
        for task, count in sorted(summary['task_distribution'].items(), key=lambda x: -x[1]):
            percentage = (count / summary['total_items']) * 100
            print(f"  {task}: {count} ({percentage:.1f}%)")
        
        print(f"\n语言分布:")
        for lang, count in summary['language_distribution'].items():
            percentage = (count / summary['total_items']) * 100
            print(f"  {lang}: {count} ({percentage:.1f}%)")
        
        print("="*60)


def main():
    """主函数"""
    agent = AgentV2()
    
    # 运行Agent
    # 可以指定特定任务类型，例如：
    # agent.run(task_types=["Q&A", "AG"])
    
    # 或者处理所有任务：
    agent.run()


if __name__ == "__main__":
    main()
