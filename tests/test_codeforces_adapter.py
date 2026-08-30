from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from codeforces_adapter import (
    build_benchmark_record,
    extract_limits_from_html,
    extract_problem_description_from_html,
    extract_samples_from_html,
    load_codeforces_package,
    materialize_problem,
    parse_problem_id,
    write_problem_package,
)
from evaluation.programming_judge import judge_programming_submission
from judge import run_submission

FIXTURE_HTML = REPO_ROOT / "tests" / "fixtures" / "codeforces" / "4A.html"
FIXTURE_METADATA = {
    "contestId": 4,
    "index": "A",
    "name": "Watermelon",
    "rating": 800,
    "tags": ["brute force", "math"],
}


class CodeforcesAdapterTests(unittest.TestCase):
    def test_parse_problem_id(self):
        ref = parse_problem_id("cf_4a")
        self.assertEqual(ref.contest_id, 4)
        self.assertEqual(ref.index, "A")
        self.assertEqual(ref.problem_id, "cf_4A")

    def test_extract_samples_and_limits_from_fixture_html(self):
        page = FIXTURE_HTML.read_text(encoding="utf-8")
        samples = extract_samples_from_html(page)
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].input_text, "8")
        self.assertEqual(samples[0].output_text, "YES")
        time_ms, memory_mb = extract_limits_from_html(page)
        self.assertEqual(time_ms, 1000)
        self.assertEqual(memory_mb, 64)
        description = extract_problem_description_from_html(page)
        self.assertIn("divide the watermelon", description)
        self.assertIn("Input", description)

    def test_write_package_and_judge_ac_solution(self):
        ref = parse_problem_id("4A")
        with self.subTest("package build"):
            destination = REPO_ROOT / "data" / "benchmarks" / "codeforces" / "packages" / "4A"
            page = FIXTURE_HTML.read_text(encoding="utf-8")
            samples = extract_samples_from_html(page)
            time_ms, memory_mb = extract_limits_from_html(page)
            write_problem_package(
                ref,
                samples=samples,
                time_ms=time_ms,
                memory_mb=memory_mb,
                destination=destination,
                metadata=FIXTURE_METADATA,
                statement_html=page,
            )
            package = load_codeforces_package(destination)
            self.assertEqual(package.problem_id, "cf_4A")
            self.assertEqual(len(package.tests_for("sample")), 1)

        solution = (
            "n = int(input())\n"
            'print("YES" if n % 2 == 0 and n > 2 else "NO")\n'
        )
        result = run_submission(package, solution, "python3", "sample")
        self.assertEqual(result.verdict, "AC")
        self.assertTrue(result.to_dict()["correct"])

        record = build_benchmark_record(
            ref,
            metadata=FIXTURE_METADATA,
            samples=samples,
            time_ms=time_ms,
            memory_mb=memory_mb,
            package_path=destination,
            repo_root=REPO_ROOT,
        )
        judged = judge_programming_submission(
            record,
            solution,
            competition_id="codeforces",
            repo_root=REPO_ROOT,
            fetch_kattis=False,
            test_scope="sample",
        )
        self.assertEqual(judged.verdict, "AC")

        wrong = judge_programming_submission(
            record,
            'print("NO")\n',
            competition_id="codeforces",
            repo_root=REPO_ROOT,
            fetch_kattis=False,
            test_scope="sample",
        )
        self.assertEqual(wrong.verdict, "WA")

    def test_materialize_offline_updates_benchmark(self):
        with self.subTest("offline materialize"):
            result = materialize_problem(
                "4A",
                repo_root=REPO_ROOT,
                force=True,
                html=FIXTURE_HTML.read_text(encoding="utf-8"),
                metadata=FIXTURE_METADATA,
            )
            self.assertFalse(result["reused"])
            record = result["benchmark_record"]
            self.assertEqual(record["problem_id"], "cf_4A")
            self.assertIn("official_bundle_path", record["evaluation"])

        benchmark_path = REPO_ROOT / "data" / "benchmarks" / "codeforces" / "benchmark.json"
        payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
        self.assertTrue(any(item["problem_id"] == "cf_4A" for item in payload))


if __name__ == "__main__":
    unittest.main()
