"""
评估模块 - GPT-5.4 Judge
使用 GPT-5.4 API 作为 Model-as-a-Judge 对 Agent 输出进行多维度评分
"""
import json
import requests
from typing import Dict, Any, Optional
from config import GPT5_API_KEY, GPT5_API_BASE, GPT5_MODEL_NAME
from core.prompts import GPT5_JUDGE_PROMPT_ZH

class GPT5Judge:
    """GPT-5.4 自动评估器"""
    
    def __init__(self, api_key: str = GPT5_API_KEY, api_base: str = GPT5_API_BASE):
        self.api_key = api_key
        self.api_base = api_base
        self.model = GPT5_MODEL_NAME
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def judge_answer(self, task_type: str, question: str, prediction: str, ground_truth: str) -> Dict[str, Any]:
        """
        对单个回答进行评分
        """
        prompt = GPT5_JUDGE_PROMPT_ZH.format(
            task_type=task_type,
            question=question,
            prediction=prediction,
            ground_truth=ground_truth
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个严谨的教育专家评估系统。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            res_data = response.json()
            content = res_data['choices'][0]['message']['content']
            
            # 解析 JSON 评分结果
            scores = json.loads(content)
            return scores
        except Exception as e:
            print(f"⚠ GPT-5.4 Evaluation failed: {e}")
            return {
                "Error": str(e),
                "Average": 0,
                "Reason": "API call failed"
            }

if __name__ == "__main__":
    # 简单测试
    judge = GPT5Judge()
    test_res = judge.judge_answer(
        "Q&A", 
        "1+1等于几？", 
        "1+1等于2", 
        "1+1=2"
    )
    print(json.dumps(test_res, indent=2, ensure_ascii=False))
