"""
难度感知决策模块 - AgentV2
根据题目特征自动判断应采用快思考还是慢思考
"""
from typing import Dict, Any
import re
from config import DIFFICULTY_KEYWORDS, SUBJECT_KEYWORDS


class DifficultyDecision:
    """
    难度感知决策器
    根据题目的学科、教育水平、问题类型等特征，决定使用快思考或慢思考
    
    决策规则（根据盘古论文的建议）：
    1. 快思考：简单问答、基础知识、小学题目
    2. 慢思考：复杂推理、高年级题目、需要分析的任务
    """
    
    def __init__(self):
        self.difficulty_keywords = DIFFICULTY_KEYWORDS
        self.subject_keywords = SUBJECT_KEYWORDS
    
    def decide(self, data_item: Any) -> str:
        """
        决定使用快思考还是慢思考
        
        Args:
            data_item: 数据项（DataItem对象）
            
        Returns:
            "fast", "slow", 或 "both"（先慢后快，根据论文建议）
        """
        # 提取特征
        features = self._extract_features(data_item)
        
        # 计算难度分数
        difficulty_score = self._calculate_difficulty(features)
        
        # 根据任务类型调整策略
        task_strategy = self._get_task_strategy(data_item.task_type)
        
        # 综合决策
        decision = self._make_decision(difficulty_score, task_strategy)
        
        return decision
    
    def _extract_features(self, data_item: Any) -> Dict[str, Any]:
        """提取题目特征"""
        features = {
            "task_type": data_item.task_type,
            "subject": data_item.subject.lower() if data_item.subject else "",
            "education_level": data_item.education_level.lower() if data_item.education_level else "",
            "question_type": data_item.question_type.lower() if data_item.question_type else "",
            "question_length": len(data_item.question),
            "prompt_length": len(data_item.prompt),
            "has_options": "选项" in data_item.question or "options" in data_item.question.lower(),
            "has_multi_choice": "多选" in data_item.question_type or "multiple" in data_item.question_type.lower(),
        }
        
        # 检测数学相关内容
        features["has_math"] = bool(
            re.search(r'[\d\+\-\*/\=\(\)]+', data_item.question) or
            any(kw in features["subject"] for kw in self.subject_keywords["math"])
        )
        
        return features
    
    def _calculate_difficulty(self, features: Dict[str, Any]) -> float:
        """
        计算难度分数 (0-1)
        0: 最简单 -> 快思考
        1: 最困难 -> 慢思考
        """
        score = 0.5  # 默认中等难度
        
        # 1. 根据教育水平调整 (+/- 0.3)
        education_level = features["education_level"]
        for keyword in self.difficulty_keywords["easy"]:
            if keyword in education_level:
                score -= 0.3
                break
        for keyword in self.difficulty_keywords["hard"]:
            if keyword in education_level:
                score += 0.3
                break
        
        # 2. 根据题目长度调整 (+/- 0.15)
        if features["question_length"] < 50:
            score -= 0.15
        elif features["question_length"] > 200:
            score += 0.15
        
        # 3. 根据题目类型调整 (+/- 0.2)
        if features["has_options"] and not features["has_multi_choice"]:
            # 单选题相对简单
            score -= 0.1
        elif features["has_multi_choice"]:
            # 多选题稍难
            score += 0.1
        elif any(kw in features["question_type"] for kw in ["解答", "分析", "证明", "solve", "analyze", "prove"]):
            # 解答题较难
            score += 0.2
        
        # 4. 数学题目需要更仔细的推理 (+0.1)
        if features["has_math"]:
            score += 0.1
        
        # 限制在 [0, 1] 范围
        return max(0.0, min(1.0, score))
    
    def _get_task_strategy(self, task_type: str) -> str:
        """
        根据任务类型获取推荐策略
        
        不同任务类型的特点：
        - question_answering: 可快可慢，取决于难度
        - automatic_grading: 需要详细分析 -> 慢思考
        - error_correction: 需要仔细对比 -> 慢思考
        - idea_prompting: 需要系统思路 -> 慢思考
        - personalized_*: 需要综合考虑 -> 慢思考
        - question_generation: 创造性任务 -> 慢思考
        - teaching_material: 系统设计 -> 慢思考
        """
        if task_type == "question_answering":
            return "adaptive"  # 根据难度自适应
        elif task_type in ["automatic_grading", "error_correction", "idea_prompting",
                           "personalized_content", "personalized_learning",
                           "question_generation", "teaching_material"]:
            return "slow"  # 强制慢思考
        else:
            return "adaptive"
    
    def _make_decision(self, difficulty_score: float, task_strategy: str) -> str:
        """
        综合决策
        
        Args:
            difficulty_score: 难度分数 (0-1)
            task_strategy: 任务策略 ("adaptive", "fast", "slow")
            
        Returns:
            "fast": 快思考
            "slow": 慢思考
            "both": 两种都执行（先慢后快，根据论文建议用慢思考引导快思考）
        """
        if task_strategy == "slow":
            return "slow"
        elif task_strategy == "fast":
            return "fast"
        else:  # adaptive
            if difficulty_score < 0.35:
                # 简单题目：快思考即可
                return "fast"
            elif difficulty_score < 0.65:
                # 中等难度：两种都做，对比效果
                return "both"
            else:
                # 困难题目：慢思考（或先慢后快）
                return "both"  # 根据论文，用慢思考引导快思考
    
    def get_decision_explanation(self, data_item: Any) -> Dict[str, Any]:
        """
        获取决策的详细解释（用于调试和分析）
        
        Returns:
            包含决策过程的详细信息
        """
        features = self._extract_features(data_item)
        difficulty_score = self._calculate_difficulty(features)
        task_strategy = self._get_task_strategy(data_item.task_type)
        decision = self._make_decision(difficulty_score, task_strategy)
        
        return {
            "decision": decision,
            "difficulty_score": difficulty_score,
            "task_strategy": task_strategy,
            "features": features,
            "reasoning": self._explain_decision(decision, difficulty_score, task_strategy)
        }
    
    def _explain_decision(self, decision: str, difficulty_score: float, task_strategy: str) -> str:
        """生成决策解释"""
        explanations = []
        
        if task_strategy == "slow":
            explanations.append(f"任务类型需要详细分析，强制使用慢思考")
        elif task_strategy == "fast":
            explanations.append(f"任务类型简单直接，使用快思考")
        else:
            explanations.append(f"难度分数: {difficulty_score:.2f}")
            if difficulty_score < 0.35:
                explanations.append("题目较简单，使用快思考")
            elif difficulty_score < 0.65:
                explanations.append("题目中等难度，使用两种思考模式对比")
            else:
                explanations.append("题目较难，使用慢思考或两种模式结合")
        
        return "; ".join(explanations)


if __name__ == "__main__":
    # 测试难度决策器
    from data_loader import DataLoader, DataItem
    
    # 创建测试数据
    test_items = [
        DataItem(
            task_type="question_answering",
            prompt="1+1等于多少？",
            question="1+1等于多少？",
            subject="数学",
            education_level="小学",
            question_type="单选题",
            lang="zh"
        ),
        DataItem(
            task_type="question_answering",
            prompt="证明勾股定理",
            question="请用至少两种方法证明勾股定理，并说明其几何意义。",
            subject="数学",
            education_level="高中",
            question_type="解答题",
            lang="zh"
        ),
        DataItem(
            task_type="automatic_grading",
            prompt="评分任务",
            question="学生作文评分",
            subject="语文",
            education_level="初中",
            question_type="作文",
            lang="zh"
        )
    ]
    
    decider = DifficultyDecision()
    
    print("="*60)
    print("难度感知决策测试")
    print("="*60)
    
    for i, item in enumerate(test_items, 1):
        print(f"\n测试 {i}:")
        print(f"  题目: {item.question[:50]}...")
        print(f"  任务类型: {item.task_type}")
        print(f"  学科: {item.subject}, 水平: {item.education_level}")
        
        explanation = decider.get_decision_explanation(item)
        print(f"  决策: {explanation['decision']}")
        print(f"  难度分数: {explanation['difficulty_score']:.2f}")
        print(f"  推理: {explanation['reasoning']}")
