# GPT-5.4 Eval Status

Date checked: 2026-03-16

## Current status

The GPT-5.4 re-judge path is implemented locally, but it is not runnable with the current provider configuration.

Relevant code paths:

- `scripts/rejudge_edubench_with_gpt5.py`
- `evaluation/openai_api.py`
- `evaluation/judge.py`

## What was verified

The current default configuration in [config.py](/opt/pangu/pangu/config.py) is:

- `GPT5_API_BASE=https://api.aicodemirror.com/v1`
- `GPT5_MODEL_NAME=gpt-5.4`

The configured secret currently looks like an Anthropic-style key:

- key prefix: `sk-ant-`

The earlier probe attempts against the configured base returned `404` for:

- `/models`
- `/chat/completions`
- `/responses`

This means the blocker is not the local scoring code. The blocker is the upstream provider configuration.

## What changed in the repo

To make this failure mode explicit and reproducible:

- `evaluation/openai_api.py` now exposes `probe_openai_compatible_api(...)`
- `scripts/rejudge_edubench_with_gpt5.py` now supports:
  - `--preflight-only`
  - `--skip-preflight`

The intended workflow is now:

```bash
python scripts/rejudge_edubench_with_gpt5.py --preflight-only
python scripts/rejudge_edubench_with_gpt5.py --sample-limit 20 --sleep-seconds 0.5
python scripts/aggregate_edubench_scores.py \
  --input-csv /opt/pangu/EduBench/data/all_data/model_eval_score/model_sampled_eval_scores.csv \
  --input-csv /opt/pangu/pangu/outputs/edubench/gpt54_model_sampled_eval_scores.csv \
  --output-json /opt/pangu/pangu/outputs/edubench/aggregated_tables.json \
  --output-md /opt/pangu/pangu/outputs/edubench/aggregated_tables.md
```

## What you need to fix

Provide all of the following:

1. A real OpenAI-compatible base URL that serves `/models` and at least one of:
   - `/chat/completions`
   - `/responses`
2. A matching API key for that provider.
3. A model name that the provider actually exposes for JSON scoring.

## Paper implication

The paper can already report:

- corrected offline deterministic metrics from saved predictions
- official EduBench sampled baseline references under the existing evaluators (`gpt-4o`, `deepseek-r1`, `deepseek-v3`, `qwq-plus`)

The paper should not claim that GPT-5.4 re-judged baseline tables are complete yet. The honest statement is:

`The GPT-5.4 re-judge pipeline is implemented, but final baseline alignment is pending a valid OpenAI-compatible provider configuration.`
