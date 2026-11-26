import csv
import json
import tempfile
import unittest
from pathlib import Path

import evaluate


class EvaluateTests(unittest.TestCase):
    def test_safe_ratio_handles_zero_denominator(self):
        self.assertEqual(evaluate.safe_ratio(0, 0), 0.0)
        self.assertEqual(evaluate.safe_ratio(3, 4), 0.75)

    def test_unrecognized_description_is_reported_not_fatal(self):
        required, optional, evidence, warning = evaluate.sections(
            "This description has no recognized requirement phrase.",
            ["Python"],
        )
        self.assertEqual(required, [])
        self.assertEqual(optional, [])
        self.assertEqual(evidence, "")
        self.assertEqual(warning, "Unrecognized requirement format")

    def test_empty_input_writes_valid_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            skills = tmp / "skills.csv"
            jobs = tmp / "jobs.csv"
            out = tmp / "out"

            skills.write_text("skill\nPython\n", encoding="utf-8")
            with jobs.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["jd_id", "description", "model_tags"])

            summary = evaluate.run(jobs, skills, out)

            self.assertEqual(summary["job_descriptions"], 0)
            self.assertEqual(summary["precision"], 0.0)
            self.assertEqual(summary["recall"], 0.0)
            self.assertTrue((out / "audit_rows.csv").exists())
            self.assertTrue((out / "tag_judgments.csv").exists())
            self.assertEqual(
                json.loads((out / "summary.json").read_text(encoding="utf-8")),
                summary,
            )

    def test_supplied_audit_metrics_are_unchanged(self):
        base = Path(__file__).parent
        with tempfile.TemporaryDirectory() as tmp:
            summary = evaluate.run(
                base / "job-descriptions-tagged.csv",
                base / "skill-list.csv",
                tmp,
            )
        self.assertEqual(summary["true_positives"], 151)
        self.assertEqual(summary["false_positives"], 49)
        self.assertEqual(summary["false_negatives"], 26)
        self.assertEqual(summary["precision"], 0.755)


if __name__ == "__main__":
    unittest.main()
