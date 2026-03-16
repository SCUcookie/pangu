"""
Build figures, tables, and metrics for the revised Pangu-ACE paper package.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image, ImageColor, ImageDraw, ImageFont

from evaluation.metrics import MetricSuite
from scripts.aggregate_edubench_scores import _build_metric_table, _build_scenario_table, _read_rows


TASK_ORDER = ["Q&A", "AG", "EC", "IP", "PCC", "PLS", "QG", "TMG"]

PREDICTION_GROUPS = {
    "full_zh": {
        "cascade_final": PROJECT_ROOT
        / "outputs/predictions/cascade_final__zh__test__paper_detached_20260315_180937__20260315_230030.jsonl",
        "rule_v2": PROJECT_ROOT
        / "outputs/predictions/rule_v2__zh__test__paper_detached_20260315_180623__20260315_190245.jsonl",
    },
    "fast_zh": {
        "1b_only": PROJECT_ROOT
        / "outputs/predictions/1b_only__zh__test__paper_fast_detached_20260315_182525__20260315_115226.jsonl",
        "7b_only": PROJECT_ROOT
        / "outputs/predictions/7b_only__zh__test__paper_fast_detached_20260315_182525__20260315_114055.jsonl",
        "rule_v2": PROJECT_ROOT
        / "outputs/predictions/rule_v2__zh__test__paper_fast_detached_20260315_182525__20260315_151723.jsonl",
        "cascade_final": PROJECT_ROOT
        / "outputs/predictions/cascade_final__zh__test__paper_fast_detached_20260315_182525__20260315_110751.jsonl",
    },
    "fast_en": {
        "1b_only": PROJECT_ROOT
        / "outputs/predictions/1b_only__en__test__paper_fast_detached_20260315_182525__20260315_133142.jsonl",
        "7b_only": PROJECT_ROOT
        / "outputs/predictions/7b_only__en__test__paper_fast_detached_20260315_182525__20260315_131906.jsonl",
        "cascade_final": PROJECT_ROOT
        / "outputs/predictions/cascade_final__en__test__paper_fast_detached_20260315_182525__20260315_123927.jsonl",
    },
    "ablation_zh": {
        "cascade_final": PROJECT_ROOT
        / "outputs/predictions/cascade_final__zh__ablation__paper_fast_detached_20260315_182525__20260315_135221.jsonl",
        "cascade_no_calibrator": PROJECT_ROOT
        / "outputs/predictions/cascade_no_calibrator__zh__ablation__paper_fast_detached_20260315_182525__20260315_141258.jsonl",
        "cascade_no_specialist_prompt": PROJECT_ROOT
        / "outputs/predictions/cascade_no_specialist_prompt__zh__ablation__paper_fast_detached_20260315_182525__20260315_143040.jsonl",
        "cascade_no_draft_conditioning": PROJECT_ROOT
        / "outputs/predictions/cascade_no_draft_conditioning__zh__ablation__paper_fast_detached_20260315_182525__20260315_145053.jsonl",
    },
}

SOURCE_DIR = PROJECT_ROOT / "outputs/paper_revision/source"
FIGURE_DIR = SOURCE_DIR / "figures"
TABLE_DIR = SOURCE_DIR / "tables"
ASSET_DIR = PROJECT_ROOT / "outputs/paper_revision/assets"
EDUBENCH_OUTPUT_DIR = PROJECT_ROOT / "outputs/edubench"
EDUBENCH_SCORE_CSV = PROJECT_ROOT.parent / "EduBench/data/all_data/model_eval_score/model_sampled_eval_scores.csv"

COLORS = {
    "ink": "#1f2937",
    "navy": "#12355b",
    "teal": "#2a9d8f",
    "orange": "#f4a261",
    "gold": "#e9c46a",
    "red": "#d1495b",
    "green": "#6c9a4d",
    "light": "#f7f3ea",
    "gray": "#d5d8dc",
    "white": "#ffffff",
    "blue_light": "#dbe7f5",
    "teal_light": "#d9efe9",
    "orange_light": "#f6d9c7",
    "green_light": "#d7ead4",
}


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    EDUBENCH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    metrics = _build_metrics()
    edubench_tables = _build_edubench_tables()
    _write_json(ASSET_DIR / "paper_metrics.json", metrics)
    _write_json(EDUBENCH_OUTPUT_DIR / "aggregated_tables.json", edubench_tables)
    (EDUBENCH_OUTPUT_DIR / "aggregated_tables.md").write_text(
        _build_edubench_markdown(edubench_tables),
        encoding="utf-8",
    )

    (TABLE_DIR / "main_full_zh.tex").write_text(_render_full_zh_table(metrics), encoding="utf-8")
    (TABLE_DIR / "fast_diag_zh.tex").write_text(_render_fast_table(metrics, group_name="fast_zh"), encoding="utf-8")
    (TABLE_DIR / "fast_diag_en.tex").write_text(_render_fast_table(metrics, group_name="fast_en"), encoding="utf-8")
    (TABLE_DIR / "ablation_zh.tex").write_text(_render_ablation_table(metrics), encoding="utf-8")
    (TABLE_DIR / "edubench_gpt4o_reference.tex").write_text(
        _render_edubench_reference_table(edubench_tables),
        encoding="utf-8",
    )

    _draw_system_overview(metrics, FIGURE_DIR / "system_overview.png")
    _draw_quality_latency(metrics, FIGURE_DIR / "quality_latency_tradeoff.png")
    _draw_routing_by_task(metrics, FIGURE_DIR / "routing_by_task.png")
    _draw_task_delta(metrics, FIGURE_DIR / "task_quality_delta.png")

    summary = {
        "paper_metrics_json": str(ASSET_DIR / "paper_metrics.json"),
        "edubench_tables_json": str(EDUBENCH_OUTPUT_DIR / "aggregated_tables.json"),
        "tables": sorted(path.name for path in TABLE_DIR.glob("*.tex")),
        "figures": sorted(path.name for path in FIGURE_DIR.glob("*.png")),
    }
    (ASSET_DIR / "build_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _build_metrics() -> Dict[str, Dict[str, Dict[str, object]]]:
    metric_suite = MetricSuite()
    output: Dict[str, Dict[str, Dict[str, object]]] = {}
    for group_name, system_files in PREDICTION_GROUPS.items():
        output[group_name] = {}
        for system_name, prediction_file in system_files.items():
            rows = _read_rescored_rows(prediction_file, metric_suite)
            aggregate = metric_suite.aggregate(rows)
            per_task = {}
            for task_key in TASK_ORDER:
                task_rows = [row for row in rows if row["task_key"] == task_key]
                if not task_rows:
                    continue
                per_task[task_key] = metric_suite.aggregate(task_rows)

            output[group_name][system_name] = {
                "prediction_file": str(prediction_file),
                "total_items": aggregate["total_items"],
                "quality_score": aggregate["quality_score"],
                "format_validity": aggregate["format_validity"],
                "latency_avg": aggregate["latency_avg"],
                "latency_p50": aggregate["latency_p50"],
                "accepted_by_1b_rate": aggregate["accepted_by_1b_rate"],
                "7b_invocation_rate": aggregate["7b_invocation_rate"],
                "estimated_cost_proxy": aggregate["estimated_cost_proxy"],
                "per_task": per_task,
            }
    return output


def _build_edubench_tables() -> Dict[str, Dict[str, Dict[str, Dict[str, float]]]]:
    rows = list(_read_rows([str(EDUBENCH_SCORE_CSV)]))
    return {
        "scenario_table": _build_scenario_table(rows),
        "metric_table": _build_metric_table(rows),
    }


def _read_rescored_rows(prediction_file: Path, metric_suite: MetricSuite) -> List[Dict]:
    rows = []
    with prediction_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(metric_suite.rescore_saved_row(json.loads(line)))
    return rows


def _write_json(path: Path, payload: Dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _render_full_zh_table(metrics: Dict[str, Dict[str, Dict[str, object]]]) -> str:
    rows = []
    for system_name in ("rule_v2", "cascade_final"):
        record = metrics["full_zh"][system_name]
        rows.append(
            " & ".join(
                [
                    _system_label(system_name),
                    str(record["total_items"]),
                    _float(record["quality_score"], 3),
                    _float(record["format_validity"], 3),
                    _float(record["latency_avg"], 2),
                    _pct(record["7b_invocation_rate"], 1),
                    _pct(record["accepted_by_1b_rate"], 1),
                ]
            )
            + r" \\"
        )
    return "\n".join(
        [
            r"\begin{tabular}{lrrrrrr}",
            r"\toprule",
            r"System & Samples & Quality & Format & Latency (s) & 7B rate & 1B accept \\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )


def _render_fast_table(metrics: Dict[str, Dict[str, Dict[str, object]]], *, group_name: str) -> str:
    system_order = ["1b_only", "rule_v2", "cascade_final", "7b_only"] if group_name == "fast_zh" else [
        "1b_only",
        "cascade_final",
        "7b_only",
    ]
    rows = []
    for system_name in system_order:
        if system_name not in metrics[group_name]:
            continue
        record = metrics[group_name][system_name]
        rows.append(
            " & ".join(
                [
                    _system_label(system_name),
                    str(record["total_items"]),
                    _float(record["quality_score"], 3),
                    _float(record["format_validity"], 3),
                    _float(record["latency_avg"], 2),
                    _pct(record["7b_invocation_rate"], 1),
                    _pct(record["accepted_by_1b_rate"], 1),
                ]
            )
            + r" \\"
        )
    return "\n".join(
        [
            r"\begin{tabular}{lrrrrrr}",
            r"\toprule",
            r"System & Samples & Quality & Format & Latency (s) & 7B rate & 1B accept \\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )


def _render_ablation_table(metrics: Dict[str, Dict[str, Dict[str, object]]]) -> str:
    rows = []
    for system_name in (
        "cascade_final",
        "cascade_no_calibrator",
        "cascade_no_specialist_prompt",
        "cascade_no_draft_conditioning",
    ):
        record = metrics["ablation_zh"][system_name]
        rows.append(
            " & ".join(
                [
                    _system_label(system_name),
                    str(record["total_items"]),
                    _float(record["quality_score"], 3),
                    _float(record["format_validity"], 3),
                    _float(record["latency_avg"], 2),
                    _pct(record["7b_invocation_rate"], 1),
                ]
            )
            + r" \\"
        )
    return "\n".join(
        [
            r"\begin{tabular}{lrrrrr}",
            r"\toprule",
            r"Variant & Samples & Quality & Format & Latency (s) & 7B rate \\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )


def _render_edubench_reference_table(tables: Dict[str, Dict[str, Dict[str, Dict[str, float]]]]) -> str:
    gpt4o_rows = tables["scenario_table"]["gpt-4o"]
    ordered = sorted(
        gpt4o_rows.items(),
        key=lambda item: item[1].get("Average", -math.inf),
        reverse=True,
    )
    lines = []
    for model_name, record in ordered:
        lines.append(
            " & ".join(
                [
                    _display_model_name(model_name),
                    _float(record.get("Average"), 2),
                    _float(record.get("Q&A"), 2),
                    _float(record.get("IP"), 2),
                    _float(record.get("AG"), 2),
                    _float(record.get("QG"), 2),
                    _float(record.get("PCC"), 2),
                ]
            )
            + r" \\"
        )
    return "\n".join(
        [
            r"\begin{tabular}{lrrrrrr}",
            r"\toprule",
            r"Model & Avg. & Q\&A & IP & AG & QG & PCC \\",
            r"\midrule",
            *lines,
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )


def _build_edubench_markdown(tables: Dict[str, Dict[str, Dict[str, Dict[str, float]]]]) -> str:
    gpt4o_rows = tables["scenario_table"]["gpt-4o"]
    ordered = sorted(
        gpt4o_rows.items(),
        key=lambda item: item[1].get("Average", -math.inf),
        reverse=True,
    )
    lines = [
        "# EduBench Reference Baselines",
        "",
        "Aggregated from the original `model_sampled_eval_scores.csv` with the GPT-4o evaluator.",
        "",
        "| Model | Average | Q&A | IP | AG | QG | PCC |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model_name, record in ordered:
        lines.append(
            "| "
            + " | ".join(
                [
                    _display_model_name(model_name),
                    _float(record.get("Average"), 2),
                    _float(record.get("Q&A"), 2),
                    _float(record.get("IP"), 2),
                    _float(record.get("AG"), 2),
                    _float(record.get("QG"), 2),
                    _float(record.get("PCC"), 2),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _draw_system_overview(metrics: Dict[str, Dict[str, Dict[str, object]]], out_path: Path) -> None:
    image, draw = _new_canvas(1800, 1080, bg=COLORS["light"])
    title_font = _font(46, bold=True)
    subtitle_font = _font(22)
    body_font = _font(26, bold=True)
    small_font = _font(20)

    draw.text((900, 56), "Pangu-ACE pipeline used in the paper revision", fill=_rgb(COLORS["navy"]), font=title_font, anchor="mm")
    draw.text(
        (900, 108),
        "A cleaner view of the implemented cascade: normalize, route, decide, refine only when needed, then validate and log.",
        fill=_rgb(COLORS["ink"]),
        font=subtitle_font,
        anchor="mm",
    )

    query = (90, 220, 400, 380)
    normalize = (470, 220, 790, 380)
    router = (860, 220, 1200, 380)
    decision = [(900, 460), (1060, 600), (900, 740), (740, 600)]
    accept = (130, 500, 520, 700)
    specialist = (1180, 500, 1680, 700)
    validator = (690, 820, 1110, 970)
    artifacts = (470, 1000, 1330, 1060)

    for box, color, text in [
        (query, COLORS["gold"], "EduBench sample\nor user query"),
        (normalize, COLORS["white"], "Request normalizer\nshared-8 schema"),
        (router, COLORS["teal_light"], "1B tutor-router\n\ndraft answer\n task family\n confidence + risk"),
        (accept, COLORS["green_light"], "Accept 1B result\n\nlow-risk sample\nno specialist call"),
        (specialist, COLORS["orange_light"], "7B specialist refinement\n\nreasoning prompts\nassessment prompts\nplanning prompts"),
        (validator, COLORS["white"], "Validator + formatter\nreject scaffolds\nrepair output shape\nsave normalized answer"),
        (artifacts, COLORS["gray"], "Saved artifacts: predictions | traces | summaries | judge cache"),
    ]:
        _rounded_box(draw, box, fill=color, outline=COLORS["ink"], radius=24, width=4)
        font = body_font
        if box == specialist:
            font = _font(24, bold=True)
        elif box == validator:
            font = _font(24, bold=True)
        elif box == artifacts:
            font = _font(24, bold=True)
        _multiline_center(draw, box, text, font=font, fill=COLORS["ink"], spacing=10)

    draw.polygon(decision, fill=_rgb(COLORS["blue_light"]), outline=_rgb(COLORS["ink"]))
    draw.line(decision + [decision[0]], fill=_rgb(COLORS["ink"]), width=4)
    _multiline_center(draw, (760, 500, 1040, 700), "Risk below\nthreshold?", font=body_font, fill=COLORS["ink"], spacing=6)

    _arrow(draw, (400, 300), (470, 300), COLORS["ink"], width=7)
    _arrow(draw, (790, 300), (860, 300), COLORS["ink"], width=7)
    _arrow(draw, (1030, 380), (1030, 480), COLORS["ink"], width=7)
    _arrow(draw, (775, 600), (520, 600), COLORS["ink"], width=7)
    _arrow(draw, (1060, 600), (1180, 600), COLORS["ink"], width=7)
    _arrow(draw, (325, 700), (760, 820), COLORS["ink"], width=7)
    _arrow(draw, (1430, 700), (1040, 820), COLORS["ink"], width=7)
    _arrow(draw, (900, 970), (900, 1000), COLORS["ink"], width=7)

    draw.text((640, 570), "yes", fill=_rgb(COLORS["green"]), font=small_font, anchor="mm")
    draw.text((1160, 570), "no", fill=_rgb(COLORS["red"]), font=small_font, anchor="mm")

    image.save(out_path)


def _draw_quality_latency(metrics: Dict[str, Dict[str, Dict[str, object]]], out_path: Path) -> None:
    image, draw = _new_canvas(1700, 1100, bg=COLORS["white"])
    title_font = _font(38, bold=True)
    label_font = _font(24)
    tick_font = _font(20)
    note_font = _font(18)

    draw.text((850, 60), "Fast diagnostic subsets: quality vs latency", fill=_rgb(COLORS["navy"]), font=title_font, anchor="mm")
    draw.text((850, 104), "Routing is selective, but the archived cascade is not yet faster than 7B-only.", fill=_rgb(COLORS["ink"]), font=label_font, anchor="mm")

    left, top, right, bottom = 200, 180, 1520, 940
    _plot_axes(draw, left, top, right, bottom, x_label="Average latency (seconds)", y_label=None)
    _grid(draw, left, top, right, bottom, x_ticks=[5, 10, 15, 20, 25, 30, 35], y_ticks=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6], x_range=(5, 35), y_range=(0.1, 0.65), tick_font=tick_font)
    draw.text((95, 150), "Rescored quality", fill=_rgb(COLORS["ink"]), font=label_font, anchor="lm")

    marker_map = {"1b_only": "square", "rule_v2": "diamond", "cascade_final": "circle", "7b_only": "triangle"}
    color_map = {"fast_zh": COLORS["orange"], "fast_en": COLORS["teal"]}
    label_prefix = {"fast_zh": "ZH", "fast_en": "EN"}

    for group_name in ("fast_zh", "fast_en"):
        for system_name, record in metrics[group_name].items():
            x = _scale(record["latency_avg"], 5, 35, left, right)
            y = _scale(record["quality_score"], 0.1, 0.65, bottom, top)
            _marker(draw, x, y, marker_map[system_name], color_map[group_name], size=16)
            draw.text((x + 18, y - 12), f"{label_prefix[group_name]} {system_name.replace('_', ' ')}", fill=_rgb(COLORS["ink"]), font=note_font)

    draw.rounded_rectangle((1180, 915, 1510, 1010), radius=14, fill=_rgb(COLORS["white"]), outline=_rgb(COLORS["gray"]), width=2)
    _marker(draw, 1215, 950, "circle", COLORS["orange"], size=10)
    draw.text((1240, 950), "ZH subset", fill=_rgb(COLORS["ink"]), font=note_font, anchor="lm")
    _marker(draw, 1215, 985, "circle", COLORS["teal"], size=10)
    draw.text((1240, 985), "EN subset", fill=_rgb(COLORS["ink"]), font=note_font, anchor="lm")

    image.save(out_path)


def _draw_routing_by_task(metrics: Dict[str, Dict[str, Dict[str, object]]], out_path: Path) -> None:
    per_task = metrics["full_zh"]["cascade_final"]["per_task"]
    image, draw = _new_canvas(1700, 1050, bg=COLORS["white"])
    title_font = _font(38, bold=True)
    tick_font = _font(22)
    note_font = _font(20)
    label_font = _font(24)

    draw.text((850, 60), "Full Chinese test: routing mix by task", fill=_rgb(COLORS["navy"]), font=title_font, anchor="mm")
    draw.text((850, 104), "Green = accepted at 1B, blue = escalated to 7B. Right-side note shows rescored quality.", fill=_rgb(COLORS["ink"]), font=label_font, anchor="mm")

    left, top, right, bottom = 240, 180, 1420, 930
    draw.line((left, bottom, right, bottom), fill=_rgb(COLORS["ink"]), width=4)
    for tick in [0.0, 0.25, 0.5, 0.75, 1.0]:
        x = _scale(tick, 0.0, 1.2, left, right)
        draw.line((x, top, x, bottom), fill=_rgb(COLORS["gray"]), width=1)
        draw.text((x, bottom + 18), f"{tick:.2f}", fill=_rgb(COLORS["ink"]), font=tick_font, anchor="ma")
    draw.text((830, 995), "Share of samples", fill=_rgb(COLORS["ink"]), font=label_font, anchor="mm")

    bar_height = 58
    gap = 26
    y = top + 30
    for task in TASK_ORDER:
        accept = per_task[task]["accepted_by_1b_rate"] or 0.0
        invoke = per_task[task]["7b_invocation_rate"] or 0.0
        quality = per_task[task]["quality_score"] or 0.0
        draw.text((150, y + bar_height / 2), task, fill=_rgb(COLORS["ink"]), font=tick_font, anchor="mm")
        x0 = left
        x1 = _scale(accept, 0.0, 1.2, left, right)
        x2 = _scale(accept + invoke, 0.0, 1.2, left, right)
        draw.rounded_rectangle((x0, y, x1, y + bar_height), radius=14, fill=_rgb(COLORS["green"]))
        draw.rounded_rectangle((x1, y, x2, y + bar_height), radius=14, fill=_rgb(COLORS["navy"]))
        draw.text((1470, y + bar_height / 2), f"Q={quality:.2f}", fill=_rgb(COLORS["ink"]), font=note_font, anchor="mm")
        y += bar_height + gap

    draw.rounded_rectangle((250, 965, 320, 995), radius=10, fill=_rgb(COLORS["green"]))
    draw.text((340, 980), "Accepted by 1B", fill=_rgb(COLORS["ink"]), font=note_font, anchor="lm")
    draw.rounded_rectangle((590, 965, 660, 995), radius=10, fill=_rgb(COLORS["navy"]))
    draw.text((680, 980), "Escalated to 7B", fill=_rgb(COLORS["ink"]), font=note_font, anchor="lm")

    image.save(out_path)


def _draw_task_delta(metrics: Dict[str, Dict[str, Dict[str, object]]], out_path: Path) -> None:
    cascade = metrics["full_zh"]["cascade_final"]["per_task"]
    rule = metrics["full_zh"]["rule_v2"]["per_task"]
    deltas = [(cascade[task]["quality_score"] or 0.0) - (rule[task]["quality_score"] or 0.0) for task in TASK_ORDER]

    image, draw = _new_canvas(1700, 1050, bg=COLORS["white"])
    title_font = _font(38, bold=True)
    tick_font = _font(22)
    note_font = _font(20)
    label_font = _font(24)

    draw.text((850, 60), "Full Chinese test: per-task quality delta vs rule_v2", fill=_rgb(COLORS["navy"]), font=title_font, anchor="mm")
    draw.text((850, 104), "Positive bars favor cascade_final; negative bars expose remaining weak points.", fill=_rgb(COLORS["ink"]), font=label_font, anchor="mm")

    left, top, right, bottom = 170, 180, 1540, 930
    y_zero = _scale(0.0, -0.35, 0.40, bottom, top)
    draw.line((left, y_zero, right, y_zero), fill=_rgb(COLORS["ink"]), width=4)
    for tick in [-0.3, -0.2, -0.1, 0.1, 0.2, 0.3]:
        y_tick = _scale(tick, -0.35, 0.40, bottom, top)
        draw.line((left, y_tick, right, y_tick), fill=_rgb(COLORS["gray"]), width=1)
        draw.text((120, y_tick), f"{tick:+.1f}", fill=_rgb(COLORS["ink"]), font=tick_font, anchor="mm")

    width = 110
    gap = 55
    x = left + 60
    for task, delta in zip(TASK_ORDER, deltas):
        x1 = x + width
        y1 = _scale(delta, -0.35, 0.40, bottom, top)
        top_y = min(y_zero, y1)
        bottom_y = max(y_zero, y1)
        color = COLORS["teal"] if delta >= 0 else COLORS["red"]
        draw.rounded_rectangle((x, top_y, x1, bottom_y), radius=14, fill=_rgb(color))
        draw.text((x + width / 2, bottom + 32), task, fill=_rgb(COLORS["ink"]), font=tick_font, anchor="mm")
        text_y = top_y - 20 if delta >= 0 else bottom_y + 20
        anchor = "mm"
        draw.text((x + width / 2, text_y), f"{delta:+.2f}", fill=_rgb(COLORS["ink"]), font=note_font, anchor=anchor)
        x += width + gap

    draw.text((850, 990), "Quality delta relative to rule_v2", fill=_rgb(COLORS["ink"]), font=label_font, anchor="mm")
    image.save(out_path)


def _new_canvas(width: int, height: int, *, bg: str) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), _rgb(bg))
    return image, ImageDraw.Draw(image)


def _plot_axes(draw: ImageDraw.ImageDraw, left: int, top: int, right: int, bottom: int, *, x_label: str, y_label: str) -> None:
    label_font = _font(24)
    draw.line((left, top, left, bottom), fill=_rgb(COLORS["ink"]), width=4)
    draw.line((left, bottom, right, bottom), fill=_rgb(COLORS["ink"]), width=4)
    draw.text(((left + right) / 2, bottom + 52), x_label, fill=_rgb(COLORS["ink"]), font=label_font, anchor="mm")
    if y_label:
        draw.text((left - 70, top - 30), y_label, fill=_rgb(COLORS["ink"]), font=label_font, anchor="mm")


def _grid(
    draw: ImageDraw.ImageDraw,
    left: int,
    top: int,
    right: int,
    bottom: int,
    *,
    x_ticks: List[float],
    y_ticks: List[float],
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    tick_font: ImageFont.ImageFont,
) -> None:
    for tick in x_ticks:
        x = _scale(tick, x_range[0], x_range[1], left, right)
        draw.line((x, top, x, bottom), fill=_rgb(COLORS["gray"]), width=1)
        draw.text((x, bottom + 18), f"{tick:g}", fill=_rgb(COLORS["ink"]), font=tick_font, anchor="ma")
    for tick in y_ticks:
        y = _scale(tick, y_range[0], y_range[1], bottom, top)
        draw.line((left, y, right, y), fill=_rgb(COLORS["gray"]), width=1)
        draw.text((left - 18, y), f"{tick:.1f}", fill=_rgb(COLORS["ink"]), font=tick_font, anchor="rm")


def _marker(draw: ImageDraw.ImageDraw, x: float, y: float, shape: str, color: str, *, size: int) -> None:
    rgb = _rgb(color)
    outline = _rgb(COLORS["ink"])
    if shape == "circle":
        draw.ellipse((x - size, y - size, x + size, y + size), fill=rgb, outline=outline, width=3)
    elif shape == "square":
        draw.rectangle((x - size, y - size, x + size, y + size), fill=rgb, outline=outline, width=3)
    elif shape == "triangle":
        draw.polygon([(x, y - size), (x - size, y + size), (x + size, y + size)], fill=rgb, outline=outline)
    elif shape == "diamond":
        draw.polygon([(x, y - size), (x - size, y), (x, y + size), (x + size, y)], fill=rgb, outline=outline)


def _rounded_box(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    *,
    fill: str,
    outline: str,
    radius: int,
    width: int,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=_rgb(fill), outline=_rgb(outline), width=width)


def _multiline_center(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: str,
    spacing: int,
) -> None:
    left, top, right, bottom = box
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = left + (right - left - text_width) / 2
    y = top + (bottom - top - text_height) / 2
    draw.multiline_text((x, y), text, font=font, fill=_rgb(fill), spacing=spacing, align="center")


def _arrow(draw: ImageDraw.ImageDraw, start: Tuple[int, int], end: Tuple[int, int], color: str, *, width: int) -> None:
    draw.line((start, end), fill=_rgb(color), width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    arrow_len = 24
    arrow_angle = math.pi / 8
    p1 = (
        end[0] - arrow_len * math.cos(angle - arrow_angle),
        end[1] - arrow_len * math.sin(angle - arrow_angle),
    )
    p2 = (
        end[0] - arrow_len * math.cos(angle + arrow_angle),
        end[1] - arrow_len * math.sin(angle + arrow_angle),
    )
    draw.polygon([end, p1, p2], fill=_rgb(color))


def _scale(value: float, domain_min: float, domain_max: float, range_min: float, range_max: float) -> float:
    if domain_max == domain_min:
        return range_min
    ratio = (value - domain_min) / (domain_max - domain_min)
    return range_min + ratio * (range_max - range_min)


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _rgb(value: str) -> Tuple[int, int, int]:
    return ImageColor.getrgb(value)


def _float(value: float | None, digits: int) -> str:
    if value is None:
        return "--"
    return f"{value:.{digits}f}"


def _pct(value: float | None, digits: int) -> str:
    if value is None:
        return "--"
    return f"{100.0 * value:.{digits}f}\\%"


def _system_label(system_name: str) -> str:
    mapping = {
        "1b_only": r"\texttt{1b\_only}",
        "7b_only": r"\texttt{7b\_only}",
        "rule_v2": r"\texttt{rule\_v2}",
        "cascade_final": r"\texttt{cascade\_final}",
        "cascade_no_calibrator": r"w/o calibrator",
        "cascade_no_specialist_prompt": r"w/o specialist prompt",
        "cascade_no_draft_conditioning": r"w/o draft conditioning",
    }
    return mapping.get(system_name, system_name.replace("_", r"\_"))


def _display_model_name(model_name: str) -> str:
    mapping = {
        "deepseek-r1": "DeepSeek R1",
        "deepseek-v3": "DeepSeek V3",
        "qwen-max": "Qwen Max",
        "qwen2.5-14b-instruct": "Qwen2.5-14B-Instruct",
        "qwen2.5-7b-instruct": "Qwen2.5-7B-Instruct",
    }
    return mapping.get(model_name, model_name)


if __name__ == "__main__":
    main()
