from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from collectors.fetch_icpc_samples import (
    _mark_sample_ready,
    collect,
    materialize_problem_package,
)
from evaluation.programming_judge import judge_programming_submission, _official_package_path
from judge import load_problem_package


class IcpcPackageMaterializeTests(unittest.TestCase):
    def test_materialize_from_flat_samples_writes_official_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sample_dir = root / "samples" / "demo_problem"
            sample_dir.mkdir(parents=True)
            (sample_dir / "one.in").write_text("2\n", encoding="utf-8")
            (sample_dir / "one.ans").write_text("4\n", encoding="utf-8")
            record = {
                "problem_id": "demo_problem",
                "kattis_id": "demo",
                "time_limit_ms": 1500,
                "memory_limit_mb": 128,
            }
            package_dir = materialize_problem_package(
                record,
                sample_dir,
                packages_root=root / "packages",
            )
            package = load_problem_package(package_dir)
            self.assertEqual(package.problem_id, "demo_problem")
            self.assertEqual(package.limits.time_ms, 1500)
            self.assertEqual(len(package.tests_for("sample")), 1)

    def test_mark_sample_ready_sets_official_bundle_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sample_dir = root / "samples" / "icpc_demo"
            sample_dir.mkdir(parents=True)
            (sample_dir / "case.in").write_text("1\n", encoding="utf-8")
            (sample_dir / "case.ans").write_text("1\n", encoding="utf-8")
            record = {"problem_id": "icpc_demo", "kattis_id": "demo"}
            _mark_sample_ready(
                record,
                sample_dir,
                ["case"],
                packages_root=root / "packages",
            )
            self.assertIn("official_bundle_path", record["evaluation"])
            bundle = root / record["evaluation"]["official_bundle_path"]
            self.assertTrue((bundle / "package.json").is_file())

    def test_existing_bottles_samples_judge_through_official_bundle(self):
        record = json.loads(
            (REPO_ROOT / "data" / "benchmarks" / "icpc" / "benchmark.json").read_text(
                encoding="utf-8"
            )
        )[0]
        sample_dir = REPO_ROOT / str(record["evaluation"]["sample_tests_path"])
        if not sample_dir.is_dir():
            self.skipTest("ICPC bottles samples are not present locally.")
        materialize_problem_package(record, sample_dir)
        record["evaluation"]["official_bundle_path"] = (
            f"data/benchmarks/icpc/packages/{record['problem_id']}"
        )
        resolved = _official_package_path(record, REPO_ROOT)
        self.assertIsNotNone(resolved)
        judged = judge_programming_submission(
            record,
            "print('not a solution')\n",
            competition_id="icpc",
            repo_root=REPO_ROOT,
            fetch_kattis=False,
            test_scope="sample",
        )
        self.assertEqual(judged.verdict, "WA")
        self.assertEqual(judged.grading_scope_label, "sample-only")

    def test_collect_refreshes_existing_samples_into_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            benchmark = root / "benchmark.json"
            benchmark.write_text(
                json.dumps(
                    [{"problem_id": "p1", "kattis_id": "one", "competition_id": "icpc"}]
                ),
                encoding="utf-8",
            )
            sample_dir = root / "samples" / "p1"
            sample_dir.mkdir(parents=True)
            (sample_dir / "a.in").write_text("3\n", encoding="utf-8")
            (sample_dir / "a.ans").write_text("9\n", encoding="utf-8")
            summary = collect(
                benchmark_path=benchmark,
                samples_root=root / "samples",
                packages_root=root / "packages",
                opener=lambda *_args, **_kwargs: self.fail("network used"),
            )
            self.assertEqual(summary["problems"][0]["status"], "existing")
            record = json.loads(benchmark.read_text(encoding="utf-8"))[0]
            self.assertIn("official_bundle_path", record["evaluation"])
            self.assertTrue(
                (root / record["evaluation"]["official_bundle_path"] / "package.json").is_file()
            )


if __name__ == "__main__":
    unittest.main()
