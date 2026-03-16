"""
Optional post-hoc judge with disk caching.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, Sequence

from config import GPT5_API_BASE, GPT5_API_KEY, GPT5_MODEL_NAME, OUTPUT_EVAL_CACHE_DIR
from core.prompts import GPT5_JUDGE_PROMPT_ZH
from evaluation.openai_api import request_json_response


class JudgeRunner:
    """Run the optional GPT judge after predictions are already saved."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = Path(cache_dir or OUTPUT_EVAL_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def judge_row(self, row: Dict) -> Dict:
        cache_key = self._cache_key(row)
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        prompt = GPT5_JUDGE_PROMPT_ZH.format(
            task_type=row["task_type"],
            question=row.get("prompt", ""),
            prediction=row["prediction"],
            ground_truth=row["ground_truth"],
        )
        payload = {
            "model": GPT5_MODEL_NAME,
            "system_prompt": "你是一个严谨的教育专家评估系统。",
            "user_prompt": prompt,
        }

        try:
            response_record = request_json_response(
                api_base=GPT5_API_BASE,
                api_key=GPT5_API_KEY,
                model_name=GPT5_MODEL_NAME,
                system_prompt=payload["system_prompt"],
                user_prompt=payload["user_prompt"],
                timeout=60,
            )
            parsed = response_record["parsed"]
            record = {
                "request": response_record["request"],
                "response": parsed,
                "api_mode": response_record["api_mode"],
            }
        except Exception as error:
            record = {
                "request": payload,
                "response": {
                    "Error": str(error),
                    "Average": 0,
                    "Reason": "judge request failed",
                },
            }

        cache_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def evaluate_rows(self, rows: Sequence[Dict]) -> list[Dict]:
        evaluated = []
        for row in rows:
            record = self.judge_row(row)
            enriched = dict(row)
            enriched["judge_score"] = record["response"].get("Average")
            enriched["judge_payload"] = record["response"]
            evaluated.append(enriched)
        return evaluated

    def _cache_key(self, row: Dict) -> str:
        payload = {
            "sample_id": row.get("sample_id"),
            "system_name": row.get("system_name", row.get("system")),
            "task_type": row.get("task_type"),
            "prediction": row.get("prediction"),
            "ground_truth": row.get("ground_truth"),
        }
        return hashlib.sha1(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
