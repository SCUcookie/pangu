# Paper Revision Bundle

This directory contains the rewritten paper source aligned with the actual archived EduBench cascade experiments.

## Contents

- `source/templateArxiv.tex`
- `source/PRIMEarxiv.sty`
- `source/references.bib`
- `source/figures/*.png`
- `source/tables/*.tex`
- `assets/paper_metrics.json`

## How the assets were generated

Run:

```bash
python /opt/pangu/pangu/scripts/build_paper_revision_assets.py
```

This regenerates:

- rescored paper metrics from saved prediction JSONL files
- main and appendix LaTeX tables
- PNG figures for the paper
- aggregated EduBench baseline tables under `outputs/edubench/`

## GPT-5.4 status

The re-judge pipeline is implemented, but the current provider configuration fails preflight:

```bash
python /opt/pangu/pangu/scripts/rejudge_edubench_with_gpt5.py --preflight-only
```

At the time of this revision, that command reports:

- `https://api.aicodemirror.com/v1/models` returns `404`
- the configured key looks like `sk-ant-*`

See:

- `/opt/pangu/pangu/docs/gpt54-eval-status.md`

## Build note

This environment does not currently provide `pdflatex`, so the source tree was not compiled to PDF inside this session. The LaTeX sources, tables, and figures are ready for compilation in an environment with a standard TeX toolchain.
