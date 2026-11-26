# Skill-tag audit — submission package

An anonymous audit of all 50 synthetic job descriptions using the supplied approved skill list.

## Files
- `evaluation_report.pdf` — one-page findings, evaluation rules, errors, first fix, and AI-use disclosure.
- `skill_audit.xlsx` — formatted Overview, JD Audit, Tag Judgments, and Rules tabs.
- `LABELING_POLICY.md` — precise written decisions and examples for correct, wrong, optional, and missing tags.
- `audit_rows.csv` — per-job required, optional, correct, wrong and missing skills and TP/FP/FN counts.
- `tag_judgments.csv` — judgments for each of the 200 predicted tags.
- `evaluate.py` — Python 3 standard-library-only calculation script.
- `job-descriptions-tagged.csv` and `skill-list.csv` — original supplied fictional inputs.
- `summary.json` — machine-readable metrics.

## Run
`python3 evaluate.py job-descriptions-tagged.csv skill-list.csv`

The script can also use the supplied CSV filenames by default:

`python3 evaluate.py`

Use `python3 evaluate.py --help` to see positional arguments and the optional
`--outdir` setting. The script validates required CSV columns, avoids zero
division on empty metric sets, and records unrecognized description formats as
`parse_warnings` instead of stopping the entire audit.

The script reproduces the CSV judgments and summary. It does not regenerate the Excel workbook or PDF.

## AI-use disclosure
ChatGPT (GPT-6) helped develop the initial rule-based labels and Python script, format the workbook, calculate metrics, and draft the report and labeling policy. The 50 JD-level outputs were subsequently walked through against the source descriptions in a guided review. The supplied row-level files and original data allow independent verification; human review does not mean the initial labels were unaided.
