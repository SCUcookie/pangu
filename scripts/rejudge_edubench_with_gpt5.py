"""
Re-score the existing EduBench sampled baseline responses with GPT-5.4.

The source CSV already contains repeated rows for multiple evaluators. This script
deduplicates by sample/candidate response, scores each unique response once with
the configured GPT-compatible endpoint, and appends rows in the same wide CSV
shape used by the EduBench repo.
"""
import argparse
import ast
import csv
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List

from config import GPT5_API_BASE, GPT5_API_KEY, GPT5_MODEL_NAME
from evaluation.openai_api import probe_openai_compatible_api, request_json_response


CSV_METRIC_COLUMNS = [
    "Domain Knowledge Accuracy",
    "Personalization, Adaptation & Learning Support",
    "Scenario Element Integration",
    "Role & Tone Consistency",
    "Error Identification & Correction Precision",
    "Motivation, Guidance & Positive Feedback",
    "Basic Factual Accuracy",
    "Reasoning Process Rigor",
    "Content Relevance & Scope Control",
    "Clarity, Simplicity & Inspiration",
    "Instruction Following & Task Completion",
    "Higher-Order Thinking & Skill Development",
]

METRIC_NAME_MAP = {
    "1.1 指令遵循与任务完成": "Instruction Following & Task Completion",
    "1.2 角色与口吻一致性": "Role & Tone Consistency",
    "1.3 内容相关性与范围控制": "Content Relevance & Scope Control",
    "1.4 场景要素融合度": "Scenario Element Integration",
    "2.1 基础事实准确性": "Basic Factual Accuracy",
    "2.2 领域知识专业性": "Domain Knowledge Accuracy",
    "2.3 推理过程严谨性": "Reasoning Process Rigor",
    "2.4 错误识别与纠正精度": "Error Identification & Correction Precision",
    "3.1 清晰易懂与表达启发": "Clarity, Simplicity & Inspiration",
    "3.2 激励引导与积极反馈": "Motivation, Guidance & Positive Feedback",
    "3.3 个性化适应与学习支持": "Personalization, Adaptation & Learning Support",
    "3.4 促进高阶思维与能力发展": "Higher-Order Thinking & Skill Development",
}

METRIC_DESCRIPTIONS = {
    "Instruction Following & Task Completion": "Whether the response completes the requested educational task faithfully.",
    "Role & Tone Consistency": "Whether the response keeps an appropriate educational role and tone.",
    "Content Relevance & Scope Control": "Whether the response stays relevant and avoids drifting beyond the task.",
    "Scenario Element Integration": "Whether important scenario elements are incorporated appropriately.",
    "Basic Factual Accuracy": "Whether the response is factually correct at a basic level.",
    "Domain Knowledge Accuracy": "Whether subject-specific knowledge is accurate and competent.",
    "Reasoning Process Rigor": "Whether the reasoning is coherent and well-supported.",
    "Error Identification & Correction Precision": "Whether corrections or grading judgments are precise.",
    "Clarity, Simplicity & Inspiration": "Whether the explanation is clear, understandable, and educationally helpful.",
    "Motivation, Guidance & Positive Feedback": "Whether the response supports learning motivation and guidance.",
    "Personalization, Adaptation & Learning Support": "Whether the response adapts to the learner or scenario well.",
    "Higher-Order Thinking & Skill Development": "Whether the response promotes analysis, transfer, or deeper skills.",
}

SYSTEM_PROMPT = (
    "You are a rigorous evaluator for educational language-model responses. "
    "Score only the requested metrics on a 1-10 scale, using integers. "
    "Return valid JSON only."
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append GPT-5.4 evaluator rows to the EduBench sampled score CSV.")
    parser.add_argument(
        "--source-csv",
        default="/opt/pangu/EduBench/data/all_data/model_eval_score/model_sampled_eval_scores.csv",
        help="Existing EduBench sampled score CSV.",
    )
    parser.add_argument(
        "--output-csv",
        default="/opt/pangu/pangu/outputs/edubench/gpt54_model_sampled_eval_scores.csv",
        help="Destination CSV for GPT-5.4 evaluator rows.",
    )
    parser.add_argument(
        "--cache-dir",
        default="/opt/pangu/pangu/outputs/edubench/gpt54_cache",
        help="Cache directory for raw judge responses.",
    )
    parser.add_argument("--eval-model", default="gpt-5.4", help="Evaluator label written to the output CSV.")
    parser.add_argument("--api-model", default=GPT5_MODEL_NAME, help="Actual model name sent to the API.")
    parser.add_argument("--sample-limit", type=int, help="Optional cap for a pilot run.")
    parser.add_argument("--language", choices=["zh", "en"], help="Optional language filter.")
    parser.add_argument("--task", help="Optional source task filter, e.g. material or Q&A.")
    parser.add_argument("--sleep-seconds", type=float, default=0.0, help="Optional pause between requests.")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Check the configured GPT-compatible endpoint and exit without scoring any rows.",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip the endpoint preflight check. Only use this if you already validated the config.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    source_csv = Path(args.source_csv)
    output_csv = Path(args.output_csv)
    cache_dir = Path(args.cache_dir)

    if not args.skip_preflight:
        preflight = probe_openai_compatible_api(
            api_base=GPT5_API_BASE,
            api_key=GPT5_API_KEY,
            timeout=20,
        )
        if args.preflight_only:
            print(json.dumps(preflight, ensure_ascii=False, indent=2))
            return
        if not preflight.get("ok"):
            raise SystemExit(
                json.dumps(
                    {
                        "error": "GPT-5.4 preflight failed",
                        "api_base": GPT5_API_BASE,
                        "api_model": args.api_model,
                        "details": preflight,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
    elif args.preflight_only:
        raise SystemExit("--preflight-only cannot be combined with --skip-preflight")

    cache_dir.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    target_rows = list(
        _iter_unique_rows(
            source_csv=source_csv,
            language=args.language,
            task=args.task,
        )
    )
    existing_keys = _load_existing_keys(output_csv)
    pending = [row for row in target_rows if _row_key(row, args.eval_model) not in existing_keys]
    if args.sample_limit is not None:
        pending = pending[: args.sample_limit]

    fieldnames = _output_fieldnames()
    rows_written = 0
    with output_csv.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if handle.tell() == 0:
            writer.writeheader()

        for row in pending:
            cache_key = _row_key(row, args.eval_model)
            cache_path = cache_dir / f"{cache_key}.json"
            if cache_path.exists():
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
            else:
                payload = _judge_row(row, api_model=args.api_model)
                cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                if args.sleep_seconds > 0:
                    time.sleep(args.sleep_seconds)

            if payload.get("error"):
                print(f"skip {row['gen_model']} qid={row['question_id']} task={row['task']}: {payload['error']}")
                continue

            writer.writerow(_build_output_row(row, payload["scores"], args.eval_model))
            rows_written += 1

    print(
        json.dumps(
            {
                "source_csv": str(source_csv),
                "output_csv": str(output_csv),
                "rows_total": len(target_rows),
                "rows_pending": len(pending),
                "rows_written": rows_written,
                "eval_model": args.eval_model,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _iter_unique_rows(source_csv: Path, language: str | None, task: str | None) -> Iterable[Dict[str, str]]:
    seen = set()
    with source_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if language and row.get("language") != language:
                continue
            if task and row.get("task") != task:
                continue
            metrics = _parse_metric_list(row.get("metrics", ""))
            metric_columns = [METRIC_NAME_MAP[item] for item in metrics if item in METRIC_NAME_MAP]
            if not metric_columns:
                continue

            normalized = {
                "question": row.get("question", ""),
                "response": row.get("response", ""),
                "gen_model": row.get("gen_model", ""),
                "task": row.get("task", ""),
                "question_id": row.get("question_id", ""),
                "language": row.get("language", ""),
                "metrics": row.get("metrics", ""),
                "metric_columns": metric_columns,
            }
            dedupe_key = _row_key(normalized, "__base__")
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            yield normalized


def _load_existing_keys(output_csv: Path) -> set[str]:
    if not output_csv.exists():
        return set()
    existing = set()
    with output_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            existing.add(_row_key(row, row.get("eval_model", "")))
    return existing


def _judge_row(row: Dict[str, str], api_model: str) -> Dict[str, object]:
    requested_metrics = []
    for column_name in row["metric_columns"]:
        requested_metrics.append(
            {
                "metric": column_name,
                "description": METRIC_DESCRIPTIONS[column_name],
            }
        )

    prompt = "\n".join(
        [
            "Evaluate the following educational response.",
            f"Task label: {row['task']}",
            f"Language: {row['language']}",
            "",
            "Question / input:",
            row["question"],
            "",
            "Candidate response:",
            row["response"],
            "",
            "Score only these metrics:",
            *[
                f"- {item['metric']}: {item['description']}"
                for item in requested_metrics
            ],
            "",
            "Return JSON with this shape:",
            '{',
            '  "scores": { "Metric Name": 1-10, "...": 1-10 },',
            '  "reason": "short explanation"',
            '}',
        ]
    )
    try:
        response_record = request_json_response(
            api_base=GPT5_API_BASE,
            api_key=GPT5_API_KEY,
            model_name=api_model,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            timeout=120,
        )
        parsed = response_record["parsed"]
        scores = parsed.get("scores", parsed)
        if not isinstance(scores, dict):
            raise ValueError("judge response did not contain a scores object")
        normalized_scores = {}
        for metric_name in row["metric_columns"]:
            if metric_name not in scores:
                raise ValueError(f"missing metric score: {metric_name}")
            normalized_scores[metric_name] = int(round(float(scores[metric_name])))
        return {
            "request": response_record["request"],
            "response": parsed,
            "scores": normalized_scores,
            "api_mode": response_record["api_mode"],
        }
    except Exception as error:
        return {
            "request": {
                "model": api_model,
                "system_prompt": SYSTEM_PROMPT,
                "user_prompt": prompt,
            },
            "error": str(error),
        }


def _build_output_row(row: Dict[str, str], scores: Dict[str, int], eval_model: str) -> Dict[str, str]:
    output = {
        "": "",
        "question": row["question"],
        "response": row["response"],
        "gen_model": row["gen_model"],
        "eval_model": eval_model,
        "task": row["task"],
        "metrics": row["metrics"],
        "question_id": row["question_id"],
        "language": row["language"],
    }
    for column in CSV_METRIC_COLUMNS:
        value = scores.get(column)
        output[column] = "" if value is None else str(value)
    return output


def _output_fieldnames() -> List[str]:
    return [
        "",
        "question",
        "response",
        "gen_model",
        "eval_model",
        "task",
        "metrics",
        "question_id",
        "language",
        *CSV_METRIC_COLUMNS,
    ]


def _parse_metric_list(raw_value: str) -> List[str]:
    if not raw_value:
        return []
    try:
        parsed = ast.literal_eval(raw_value)
    except Exception:
        return []
    return [str(item) for item in parsed]


def _row_key(row: Dict[str, str], eval_model: str) -> str:
    identity = {
        "question": row.get("question", ""),
        "response": row.get("response", ""),
        "gen_model": row.get("gen_model", ""),
        "eval_model": eval_model,
        "task": row.get("task", ""),
        "question_id": row.get("question_id", ""),
        "language": row.get("language", ""),
    }
    return hashlib.sha1(json.dumps(identity, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    main()
