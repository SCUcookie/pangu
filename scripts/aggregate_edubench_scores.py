"""
Aggregate one or more EduBench score CSVs into paper-ready tables.
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List


CSV_METRIC_COLUMNS = [
    "Basic Factual Accuracy",
    "Clarity, Simplicity & Inspiration",
    "Content Relevance & Scope Control",
    "Domain Knowledge Accuracy",
    "Error Identification & Correction Precision",
    "Higher-Order Thinking & Skill Development",
    "Instruction Following & Task Completion",
    "Motivation, Guidance & Positive Feedback",
    "Personalization, Adaptation & Learning Support",
    "Reasoning Process Rigor",
    "Role & Tone Consistency",
    "Scenario Element Integration",
]

METRIC_ABBREVIATIONS = {
    "Basic Factual Accuracy": "BFA",
    "Clarity, Simplicity & Inspiration": "CSI",
    "Content Relevance & Scope Control": "CRSC",
    "Domain Knowledge Accuracy": "DKA",
    "Error Identification & Correction Precision": "EICP",
    "Higher-Order Thinking & Skill Development": "HOTS",
    "Instruction Following & Task Completion": "IFTC",
    "Motivation, Guidance & Positive Feedback": "MGP",
    "Personalization, Adaptation & Learning Support": "PAS",
    "Reasoning Process Rigor": "RPR",
    "Role & Tone Consistency": "RTC",
    "Scenario Element Integration": "SEI",
}

TASK_TO_SCENARIO = {
    "Q&A": "Q&A",
    "design": "PLS",
    "error_correct": "EC",
    "helper": "IP",
    "judge": "AG",
    "material": "TMG",
    "mood": "ES",
    "question_gen": "QG",
    "student_profile": "PCC",
}

SCENARIO_ORDER = ["Q&A", "PLS", "EC", "IP", "AG", "TMG", "ES", "QG", "PCC"]
GEN_MODEL_ORDER = [
    "deepseek-r1",
    "deepseek-v3",
    "qwen-max",
    "qwen2.5-14b-instruct",
    "qwen2.5-7b-instruct",
]
EVAL_MODEL_ORDER = ["deepseek-r1", "deepseek-v3", "gpt-4o", "gpt-5.4", "qwq-plus"]
DISPLAY_NAMES = {
    "deepseek-r1": "DeepSeek R1",
    "deepseek-v3": "DeepSeek V3",
    "qwen-max": "Qwen Max",
    "qwen2.5-14b-instruct": "Qwen2.5-14B-Instruct",
    "qwen2.5-7b-instruct": "Qwen2.5-7B-Instruct",
    "gpt-4o": "GPT-4o",
    "gpt-5.4": "GPT-5.4",
    "qwq-plus": "QwQ-Plus",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate EduBench evaluator CSVs into scenario and metric tables.")
    parser.add_argument(
        "--input-csv",
        action="append",
        required=True,
        help="One or more input CSV files. Pass the original EduBench CSV plus any appended evaluator CSVs.",
    )
    parser.add_argument(
        "--output-json",
        default="/opt/pangu/pangu/outputs/edubench/aggregated_tables.json",
        help="Output JSON path.",
    )
    parser.add_argument(
        "--output-md",
        default="/opt/pangu/pangu/outputs/edubench/aggregated_tables.md",
        help="Output Markdown path.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    rows = list(_read_rows(args.input_csv))
    tables = {
        "scenario_table": _build_scenario_table(rows),
        "metric_table": _build_metric_table(rows),
    }

    json_path = Path(args.output_json)
    md_path = Path(args.output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(tables), encoding="utf-8")

    print(
        json.dumps(
            {
                "rows": len(rows),
                "output_json": str(json_path),
                "output_md": str(md_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _read_rows(paths: List[str]) -> Iterable[Dict[str, str]]:
    for raw_path in paths:
        path = Path(raw_path)
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if not row.get("eval_model") or not row.get("gen_model"):
                    continue
                yield row


def _build_scenario_table(rows: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, Dict[str, float]]]:
    grouped: Dict[str, Dict[str, Dict[str, List[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for row in rows:
        scenario = TASK_TO_SCENARIO.get(row.get("task", ""))
        if not scenario:
            continue
        row_average = _row_average(row)
        if row_average is None:
            continue
        grouped[row["eval_model"]][row["gen_model"]][scenario].append(row_average)

    table: Dict[str, Dict[str, Dict[str, float]]] = {}
    for eval_model, model_payload in grouped.items():
        table[eval_model] = {}
        for gen_model, scenario_payload in model_payload.items():
            row = {}
            scenario_means = []
            for scenario in SCENARIO_ORDER:
                values = scenario_payload.get(scenario, [])
                if values:
                    scenario_mean = round(mean(values), 2)
                    row[scenario] = scenario_mean
                    scenario_means.append(scenario_mean)
            row["Average"] = round(mean(scenario_means), 2) if scenario_means else None
            table[eval_model][gen_model] = row
    return table


def _build_metric_table(rows: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, Dict[str, float]]]:
    grouped: Dict[str, Dict[str, Dict[str, List[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for row in rows:
        for metric in CSV_METRIC_COLUMNS:
            value = _parse_float(row.get(metric, ""))
            if value is None:
                continue
            grouped[row["eval_model"]][row["gen_model"]][metric].append(value)

    table: Dict[str, Dict[str, Dict[str, float]]] = {}
    for eval_model, model_payload in grouped.items():
        table[eval_model] = {}
        for gen_model, metric_payload in model_payload.items():
            row = {}
            metric_means = []
            for metric in CSV_METRIC_COLUMNS:
                values = metric_payload.get(metric, [])
                if values:
                    metric_mean = round(mean(values), 2)
                    row[METRIC_ABBREVIATIONS[metric]] = metric_mean
                    metric_means.append(metric_mean)
            row["Average"] = round(mean(metric_means), 2) if metric_means else None
            table[eval_model][gen_model] = row
    return table


def _row_average(row: Dict[str, str]) -> float | None:
    values = [_parse_float(row.get(metric, "")) for metric in CSV_METRIC_COLUMNS]
    values = [value for value in values if value is not None]
    if not values:
        return None
    return mean(values)


def _parse_float(raw_value: str) -> float | None:
    if raw_value in (None, ""):
        return None
    try:
        return float(raw_value)
    except Exception:
        return None


def _build_markdown(tables: Dict[str, Dict[str, Dict[str, Dict[str, float]]]]) -> str:
    lines = [
        "# EduBench Aggregated Tables",
        "",
        "## Scenario Table",
        "",
        "| Evaluator | Model | " + " | ".join(SCENARIO_ORDER) + " | Average |",
        "| --- | --- | " + " | ".join(["---:"] * (len(SCENARIO_ORDER) + 1)) + " |",
    ]
    for eval_model in _ordered_keys(tables["scenario_table"], EVAL_MODEL_ORDER):
        model_payload = tables["scenario_table"][eval_model]
        first = True
        for gen_model in _ordered_keys(model_payload, GEN_MODEL_ORDER):
            row = model_payload[gen_model]
            evaluator_cell = DISPLAY_NAMES.get(eval_model, eval_model) if first else ""
            first = False
            values = [row.get(column) for column in SCENARIO_ORDER] + [row.get("Average")]
            rendered = ["" if value is None else f"{value:.2f}" for value in values]
            lines.append(
                f"| {evaluator_cell} | {DISPLAY_NAMES.get(gen_model, gen_model)} | " + " | ".join(rendered) + " |"
            )

    lines.extend(
        [
            "",
            "## Metric Table",
            "",
            "| Evaluator | Model | "
            + " | ".join(METRIC_ABBREVIATIONS[metric] for metric in CSV_METRIC_COLUMNS)
            + " | Average |",
            "| --- | --- | " + " | ".join(["---:"] * (len(CSV_METRIC_COLUMNS) + 1)) + " |",
        ]
    )
    metric_headers = [METRIC_ABBREVIATIONS[metric] for metric in CSV_METRIC_COLUMNS]
    for eval_model in _ordered_keys(tables["metric_table"], EVAL_MODEL_ORDER):
        model_payload = tables["metric_table"][eval_model]
        first = True
        for gen_model in _ordered_keys(model_payload, GEN_MODEL_ORDER):
            row = model_payload[gen_model]
            evaluator_cell = DISPLAY_NAMES.get(eval_model, eval_model) if first else ""
            first = False
            values = [row.get(column) for column in metric_headers] + [row.get("Average")]
            rendered = ["" if value is None else f"{value:.2f}" for value in values]
            lines.append(
                f"| {evaluator_cell} | {DISPLAY_NAMES.get(gen_model, gen_model)} | " + " | ".join(rendered) + " |"
            )

    return "\n".join(lines)


def _ordered_keys(mapping: Dict[str, object], preferred_order: List[str]) -> List[str]:
    preferred = [key for key in preferred_order if key in mapping]
    remaining = sorted(key for key in mapping if key not in preferred)
    return preferred + remaining


if __name__ == "__main__":
    main()
