"""Offline regressions for edition integrity and contestant/judge separation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import requests
from collectors.iypt_sources import collect_one, edition_links, normalize_legacy_encoding, title_year
from codeforces_adapter import materialize_problem
from dataset_catalog import complete_metadata
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
from scripts.build_data_packages import build_packages


class DatasetIntegrityRepairTests(unittest.TestCase):
    def test_edition_comes_from_title_not_upload_year(self):
        self.assertEqual(title_year("Problems for the 38th IYPT 2025\nApproved in 2024"), 2025)
        self.assertIsNone(title_year("https://iypt.org/wp-content/uploads/2024/problems2025.pdf"))

    def test_index_ignores_navigation(self):
        body = '<nav><a href="/wrong">1988</a></nav><div class="entry-content">'
        body += ''.join(f'<a href="/problems/edition-{y}/">{y}</a>' for y in range(1988, 2027)) + '</div>'
        self.assertEqual(edition_links(body.encode())[1988], "https://iypt.org/problems/edition-1988/")

    def test_broken_old_pdf_falls_back_to_same_edition_article(self):
        response = requests.Response()
        response.status_code = 200
        response.url = "https://iypt.org/problems/edition-2012/"
        response._content = ('<div class="entry-content"><h1>Problems for the 25th IYPT 2012</h1>'
                             '<a href="/old/problems2012.pdf">PDF</a><p>' + 'Investigate the experiment. '*40 + '</p></div>').encode()
        with tempfile.TemporaryDirectory() as directory, patch("collectors.iypt_sources.get", side_effect=[response, requests.HTTPError("404")]):
            source = collect_one(Path(directory), 2012, response.url)
            self.assertEqual(source["format"], "publisher_html_with_local_images")
            self.assertEqual(title_year(source["problem_description"]), 2012)

    def test_reversible_encoding_repair_preserves_correct_math(self):
        self.assertEqual(normalize_legacy_encoding("n\u00e2\u2030\u00a410; n\u00c3\u2014n; \u00ce\u00b1"), "n\u226410; n\u00d7n; \u03b1")
        correct = "caf\u00e9, \u2264, \u03b1, \u00d7 and ordinary ASCII"
        self.assertEqual(normalize_legacy_encoding(correct), correct)

    def test_curated_split_and_license_are_preserved(self):
        row = dict(problem_id="example", split="test", eval_unit="question", license={"status": "curated"})
        with tempfile.TemporaryDirectory() as directory:
            complete_metadata(row, "codeforces", Path(directory))
        self.assertEqual(row["split"], "test")
        self.assertEqual(row["license"], {"status": "curated"})
        self.assertEqual(row["evaluation"]["scorecard_key"], "example")

    def test_codeforces_materialization_and_cache_recovery_are_isolated(self):
        page = (ROOT / "tests/fixtures/codeforces/4A.html").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = materialize_problem("4A", repo_root=root, html=page, metadata={"name": "Watermelon"})
            record = result["benchmark_record"]
            self.assertEqual(record["eval_unit"], "problem")
            self.assertEqual(record["split"], "unspecified")
            self.assertEqual(record["evaluation"]["scorecard_key"], "cf_4A")
            self.assertEqual(record["evaluation"]["test_scope"], "sample_only_local")
            benchmark = root / "data/benchmarks/codeforces/benchmark.json"
            benchmark.unlink()
            recovered = materialize_problem("4A", repo_root=root)
            self.assertTrue(recovered["reused"])
            self.assertEqual(json.loads(benchmark.read_text())[0]["sample_count"], 1)
            self.assertIn("divide the watermelon", recovered["benchmark_record"]["problem_description"])

    def test_task_pack_excludes_judge_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "problem.pdf").write_bytes(b"contestant problem")
            (root / "archive.pdf").write_bytes(b"problem and SECRET SOLUTION")
            digest = lambda p: hashlib.sha256((root / p).read_bytes()).hexdigest()
            row = dict(problem_id="demo_2009", year=2009, team_size=6, eval_unit="session", split="unspecified",
                source_file="problem.pdf", solution_file="archive.pdf", problem_description="Solve the task",
                evaluation=dict(status="ready", evaluator_id="gold_answer_v1"),
                assets=[dict(path="problem.pdf", role="agent_visible", sha256=digest("problem.pdf")),
                        dict(path="archive.pdf", role="judge_only", sha256=digest("archive.pdf"))])
            index = {"olympiads": [dict(id="demo", benchmark_path="data/benchmarks/demo/benchmark.json", rule_card_path="data/rules/demo")]}
            rules = {"demo": dict(competition={"rules_text": "Use the supplied problem", "deliverable": {}}, collaboration={}, evaluation={})}
            stage = root / "stage"
            other = {**row, "problem_id": "DEMO_2009"}
            build_packages(root, stage, index, {"demo": [row, other]}, rules, digest)
            for layout in ("base", "last_exam"):
                cards = json.loads((stage / layout / "task_cards.json").read_text(encoding="utf-8"))["tasks"]
                self.assertEqual(len({c["source_repo_path"].casefold() for c in cards}), 2)
                for card in cards:
                    files = list((stage / layout / card["source_repo_path"] / "base/input").rglob("*"))
                    self.assertTrue(any(p.name == "problem.pdf" for p in files))
                    self.assertFalse(any(p.name == "archive.pdf" for p in files))
                    self.assertFalse(any(b"SECRET SOLUTION" in p.read_bytes() for p in files if p.is_file()))

    def test_hmmt_2024_uses_printed_weights(self):
        rows = json.loads((ROOT / "data/benchmarks/hmmt_guts/benchmark.json").read_text(encoding="utf-8"))
        row = next(r for r in rows if r["problem_id"] == "hmmt_guts_2024")
        parts = load_gold_parts(row["gold_label"])
        self.assertEqual(sum(p.points for p in parts), 400)
        submission = "\n".join(f"{p.id}. {p.expected}" for p in parts[1:])
        result = GoldAnswerEvaluator(parts=parts, submission_text=submission).evaluate()
        self.assertEqual(result.max_score, 400)
        self.assertEqual(result.total_score, 400-parts[0].points)


if __name__ == "__main__":
    unittest.main()
