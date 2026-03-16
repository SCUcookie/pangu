"""
Deterministic CPU-side metrics for saved prediction rows.
"""
from statistics import mean, median
from typing import Any, Dict, List, Sequence

from core.schemas import NormalizedSample
from services.output_parser import OutputParser


class MetricSuite:
    """Compute simple deterministic metrics and aggregates."""

    OPEN_TASK_KEYS = {"IP", "PCC", "PLS", "QG", "TMG"}
    ROUTER_SCHEMA_KEYS = {
        "predicted_task_family",
        "predicted_subject",
        "draft_answer",
        "confidence_label",
        "confidence_score",
        "format_signals",
        "tool_hint",
        "predicted_task_type",
        "predicted_task_key",
        "predicted_task",
    }
    PLACEHOLDER_PATTERNS = (
        "draft answer",
        "draft_answer",
        "your draft answer",
        "placeholder",
        "1b draft",
        "1b 草稿",
        "待补充",
    )
    SCAFFOLD_PATTERNS = (
        "predicted_task_",
        "task_key",
        "task_type",
        "expected_output_format",
        "confidence_label",
        "confidence_score",
        "format_signals",
        "contract_ok",
        "tool_hint",
        "output format",
        "output valid json",
        "请根据以上信息",
        "根据已知任务信息",
        "请输出一个符合要求的 json",
    )

    def __init__(self, output_parser: OutputParser | None = None):
        self.output_parser = output_parser or OutputParser()

    def score_prediction(self, sample, prediction, trace) -> Dict[str, Any]:
        format_validity = bool(trace.get("format_valid"))
        task_match = None
        if sample.task_key == "Q&A" and isinstance(prediction, dict):
            direct_answer = str(prediction.get("direct_answer", "")).strip().lower()
            gold = str(sample.ground_truth).strip().lower()
            task_match = direct_answer == gold
        elif sample.task_key == "AG" and isinstance(prediction, dict):
            task_match = str(prediction.get("score")) == str(sample.ground_truth.get("score"))
        elif sample.task_key == "EC" and isinstance(prediction, dict):
            gold = sample.ground_truth.get("corrected_answer")
            task_match = str(prediction.get("corrected_answer")) == str(gold)

        content_substance = (
            self._open_response_has_substance(sample.task_key, prediction)
            if sample.task_key in self.OPEN_TASK_KEYS
            else None
        )
        deterministic_quality = self._deterministic_quality(
            sample.task_key,
            task_match,
            format_validity,
            content_substance,
        )
        return {
            "sample_id": sample.sample_id,
            "task_key": sample.task_key,
            "route": trace.get("route"),
            "format_validity": format_validity,
            "task_match": task_match,
            "content_substance": content_substance,
            "deterministic_quality": deterministic_quality,
            "latency_seconds": float(trace.get("latency_seconds", 0.0)),
            "accepted_by_1b": trace.get("accepted_by_1b"),
            "7b_invocation": bool(trace.get("seven_b_invoked")),
        }

    def rescore_saved_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        sample = self._sample_from_row(row)
        normalized = self.output_parser.repair_or_normalize(sample, row.get("prediction"))
        seven_b_invoked = row.get("seven_b_invoked")
        if seven_b_invoked is None:
            seven_b_invoked = row.get("7b_invocation")
        if seven_b_invoked is None:
            seven_b_invoked = row.get("accepted_by_1b") is False or int(row.get("tokens_7b", 0) or 0) > 0

        trace = {
            "route": row.get("route"),
            "format_valid": not normalized.get("errors"),
            "latency_seconds": float(row.get("latency_seconds", 0.0)),
            "accepted_by_1b": row.get("accepted_by_1b"),
            "seven_b_invoked": bool(seven_b_invoked),
        }

        rescored = dict(row)
        rescored["prediction"] = normalized["normalized_prediction"]
        rescored["format_valid"] = trace["format_valid"]
        rescored.update(self.score_prediction(sample, rescored["prediction"], trace))
        rescored["seven_b_invoked"] = trace["seven_b_invoked"]
        return rescored

    def aggregate(self, rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(rows)
        latencies = [float(row.get("latency_seconds", 0.0)) for row in rows]
        tokens_1b = [int(row.get("tokens_1b", 0)) for row in rows]
        tokens_7b = [int(row.get("tokens_7b", 0)) for row in rows]
        format_valid = sum(1 for row in rows if row.get("format_validity"))
        accepted_by_1b_denominator = sum(1 for row in rows if row.get("accepted_by_1b") is not None)
        accepted_by_1b_numerator = sum(1 for row in rows if row.get("accepted_by_1b"))
        seven_b_invocations = sum(1 for row in rows if row.get("7b_invocation"))
        comparable_rows = [row for row in rows if row.get("task_match") is not None]
        judge_scores = [float(row.get("judge_score")) for row in rows if row.get("judge_score") is not None]
        quality_values = [self._row_quality_value(row) for row in rows if self._row_quality_value(row) is not None]
        accepted_rows = [row for row in rows if row.get("accepted_by_1b") is True]
        escalated_rows = [row for row in rows if row.get("accepted_by_1b") is False or row.get("7b_invocation")]
        task_match_rate = (
            sum(1 for row in comparable_rows if row.get("task_match")) / len(comparable_rows)
            if comparable_rows
            else None
        )
        return {
            "total_items": total,
            "quality_score": mean(quality_values) if quality_values else None,
            "format_validity": (format_valid / total) if total else 0.0,
            "task_match_rate": task_match_rate,
            "latency_avg": mean(latencies) if latencies else 0.0,
            "latency_p50": median(latencies) if latencies else 0.0,
            "latency_p90": self._percentile(latencies, 0.90),
            "accepted_by_1b_rate": (
                accepted_by_1b_numerator / accepted_by_1b_denominator if accepted_by_1b_denominator else None
            ),
            "accepted_by_1b_quality": self._mean_quality(accepted_rows),
            "escalated_quality": self._mean_quality(escalated_rows),
            "7b_invocation_rate": (seven_b_invocations / total) if total else 0.0,
            "tokens_1b_avg": mean(tokens_1b) if tokens_1b else 0.0,
            "tokens_7b_avg": mean(tokens_7b) if tokens_7b else 0.0,
            "estimated_cost_proxy": self._estimated_cost_proxy(rows),
            "judge_score_avg": mean(judge_scores) if judge_scores else None,
        }

    def _percentile(self, values: Sequence[float], ratio: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        index = int((len(ordered) - 1) * ratio)
        return ordered[index]

    def _deterministic_quality(
        self,
        task_key: str,
        task_match: Any,
        format_validity: bool,
        content_substance: bool | None,
    ) -> float | None:
        if task_match is not None:
            return 1.0 if task_match else 0.0
        if task_key in self.OPEN_TASK_KEYS:
            return 1.0 if format_validity and bool(content_substance) else 0.0
        return None

    def _row_quality_value(self, row: Dict[str, Any]) -> float | None:
        if row.get("judge_score") is not None:
            return float(row["judge_score"])
        if row.get("deterministic_quality") is not None:
            return float(row["deterministic_quality"])
        return None

    def _mean_quality(self, rows: Sequence[Dict[str, Any]]) -> float | None:
        values = [self._row_quality_value(row) for row in rows if self._row_quality_value(row) is not None]
        return mean(values) if values else None

    def _estimated_cost_proxy(self, rows: Sequence[Dict[str, Any]]) -> float:
        if not rows:
            return 0.0
        weighted_tokens = []
        for row in rows:
            weighted_tokens.append(int(row.get("tokens_1b", 0)) + 7 * int(row.get("tokens_7b", 0)))
        return mean(weighted_tokens)

    def _sample_from_row(self, row: Dict[str, Any]) -> NormalizedSample:
        return NormalizedSample(
            sample_id=str(row.get("sample_id", "")),
            task_key=str(row.get("task_key", "")),
            task_type=str(row.get("task_type", "")),
            task_family=str(row.get("task_family", "")),
            subject=str(row.get("subject", "")),
            education_level=str(row.get("education_level", "")),
            lang=str(row.get("lang", "")),
            question=str(row.get("question", "") or row.get("prompt", "")),
            prompt_text=str(row.get("prompt", "") or row.get("question", "")),
            expected_output_format=str(row.get("expected_output_format", "")),
            ground_truth=row.get("ground_truth"),
            metadata={
                "source_file": row.get("source_file", ""),
                "source_row": row.get("source_row", 0),
            },
        )

    def _open_response_has_substance(self, task_key: str, prediction: Any) -> bool:
        if not isinstance(prediction, dict):
            return False
        if task_key == "IP":
            return self._value_has_substance(prediction.get("hints"), min_chars=8)
        if task_key == "PCC":
            return self._value_has_substance(prediction.get("learning_path"), min_chars=8) and self._value_has_substance(
                prediction.get("personalized_suggestions"),
                min_chars=8,
            )
        if task_key == "PLS":
            return self._value_has_substance(prediction.get("personalized_learning_content"), min_chars=8)
        if task_key == "QG":
            return (
                self._value_has_substance(prediction.get("generated_question"), min_chars=8)
                and self._value_has_substance(prediction.get("answer"), min_chars=1)
                and self._value_has_substance(prediction.get("rationale"), min_chars=8)
            )
        if task_key == "TMG":
            return all(
                self._value_has_substance(prediction.get(key), min_chars=8)
                for key in ("objectives", "key_points", "classroom_activity_design")
            )
        return False

    def _value_has_substance(self, value: Any, *, min_chars: int) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            text = value.strip()
            lowered = text.lower()
            if len(text) < min_chars:
                return False
            if any(pattern in lowered for pattern in self.PLACEHOLDER_PATTERNS):
                return False
            if any(pattern in lowered for pattern in self.SCAFFOLD_PATTERNS):
                return False
            return True
        if isinstance(value, list):
            return any(self._value_has_substance(item, min_chars=min_chars) for item in value)
        if isinstance(value, dict):
            if self._looks_like_router_schema_dict(value):
                return False
            return any(self._value_has_substance(item, min_chars=min_chars) for item in value.values())
        return True

    def _looks_like_router_schema_dict(self, value: Dict[str, Any]) -> bool:
        keys = {str(key) for key in value.keys()}
        return len(keys & self.ROUTER_SCHEMA_KEYS) >= 3 or {"draft_answer", "predicted_task_family"} <= keys
