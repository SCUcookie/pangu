import unittest

from core.schemas import NormalizedSample
from evaluation.metrics import MetricSuite
from services.output_parser import OutputParser


def _sample(task_key: str, ground_truth):
    return NormalizedSample(
        sample_id=f"sample-{task_key}",
        task_key=task_key,
        task_type="teaching_material" if task_key == "TMG" else "personalized_learning",
        task_family="planning",
        subject="语文",
        education_level="初中",
        lang="zh",
        question="示例问题",
        prompt_text="示例提示",
        expected_output_format="json",
        ground_truth=ground_truth,
        metadata={},
    )


class ParserMetricRegressionTest(unittest.TestCase):
    def test_pls_placeholder_is_marked_invalid(self):
        parser = OutputParser()
        sample = _sample("PLS", ground_truth={})

        result = parser.repair_or_normalize(
            sample,
            {"personalized_learning_content": "draft_answer"},
        )

        self.assertEqual(
            result["normalized_prediction"]["personalized_learning_content"],
            "draft_answer",
        )
        self.assertEqual(result["errors"], ["missing_key:personalized_learning_content"])

    def test_pls_router_wrapped_payload_is_salvaged(self):
        parser = OutputParser()
        sample = _sample("PLS", ground_truth={})

        result = parser.repair_or_normalize(
            sample,
            {
                "personalized_learning_content": {
                    "predicted_task_family": "planning",
                    "predicted_subject": "科学",
                    "draft_answer": "设计一个分层实验任务包，先做观察再做记录。",
                    "confidence_label": "high",
                    "confidence_score": 0.9,
                    "format_signals": {"contract_ok": True},
                }
            },
        )

        self.assertEqual(result["errors"], [])
        self.assertEqual(
            result["normalized_prediction"]["personalized_learning_content"],
            "设计一个分层实验任务包，先做观察再做记录。",
        )

    def test_metric_suite_rejects_placeholder_open_task_even_if_format_flag_is_true(self):
        metric_suite = MetricSuite()
        sample = _sample("PLS", ground_truth={})

        metric_row = metric_suite.score_prediction(
            sample,
            {"personalized_learning_content": "draft_answer"},
            {
                "route": "1b_accept",
                "format_valid": True,
                "latency_seconds": 1.0,
                "accepted_by_1b": True,
                "seven_b_invoked": False,
            },
        )

        self.assertFalse(metric_row["content_substance"])
        self.assertEqual(metric_row["deterministic_quality"], 0.0)

    def test_rescore_saved_row_revalidates_stale_placeholder_predictions(self):
        metric_suite = MetricSuite()
        row = {
            "sample_id": "sample-PLS",
            "task_key": "PLS",
            "task_type": "personalized_learning",
            "task_family": "planning",
            "subject": "语文",
            "education_level": "初中",
            "lang": "zh",
            "question": "示例问题",
            "prompt": "示例提示",
            "expected_output_format": "json",
            "ground_truth": {},
            "prediction": {"personalized_learning_content": "draft_answer"},
            "route": "1b_accept",
            "accepted_by_1b": True,
            "latency_seconds": 1.2,
            "tokens_1b": 120,
            "tokens_7b": 0,
            "format_valid": True,
            "format_validity": True,
            "deterministic_quality": 1.0,
        }

        rescored = metric_suite.rescore_saved_row(row)

        self.assertFalse(rescored["format_valid"])
        self.assertFalse(rescored["format_validity"])
        self.assertEqual(rescored["deterministic_quality"], 0.0)


if __name__ == "__main__":
    unittest.main()
