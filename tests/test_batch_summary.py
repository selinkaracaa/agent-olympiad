"""Batch exports must not trust results merely because they are on disk."""
from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import run_otc_gold_suite as gold
import run_otc_arml_science_bowl as focused
import contest_batch_summary as summary_module
from contest_config import ContestRunConfig
from contest_manifest import ContestManifest
from contest_run_identity import build_run_identity


class BatchSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def identity(self, name="current", model="new"):
        return build_run_identity(
            ContestManifest(name, "science_bowl", ()),
            ContestRunConfig("decentralized", 3, 3),
            execution={"model": model}, evaluation={}, source_root=self.root / "source",
        )

    def result(self, identity, graded=True):
        settings = identity["settings"]
        return {
            **{key: settings[key] for key in
               ("session_id", "competition_id", "protocol_version", "action_set_version")},
            "system_variant": settings["config"]["system_variant"],
            "run_identity": identity,
            "grade": {"graded": graded, "score": 1 if graded else None, "max_score": 2},
            "metrics": {"task_utility": 0.5 if graded else None},
            "session_checkpoint": {"final_summary": {}},
            "budget": {"turns_used": 3},
        }

    def write_result(self, identity, payload=None):
        run_dir = self.root / identity["settings"]["session_id"]
        run_dir.mkdir(exist_ok=True)
        path = run_dir / "contest_session.json"
        path.write_text(json.dumps(payload if payload is not None else self.result(identity)),
                        encoding="utf-8")
        return path

    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    def job(self, identity, status="ok"):
        return {"problem_id": identity["settings"]["session_id"],
                "status": status, "run_identity": identity}

    def test_unchecked_old_result_cannot_enter_either_batch_summary(self):
        for batch in (gold, focused):
            with self.subTest(batch=batch.__name__), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                run_dir = root / "later-job"
                run_dir.mkdir()
                path = run_dir / "contest_session.json"
                path.write_text(json.dumps({
                    "grade": {"graded": True, "score": 99, "max_score": 99},
                    "metrics": {"task_utility": 1},
                }), encoding="utf-8")
                original = path.read_bytes()
                output = batch.summarize(root, ["later-job"])
                with output.open(encoding="utf-8", newline="") as handle:
                    row = next(csv.DictReader(handle, delimiter="\t"))
                self.assertEqual(row["task_utility"], "")
                self.assertEqual(row["status"], "pending")
                self.assertEqual(path.read_bytes(), original)

    def test_both_batches_use_the_same_exporter(self):
        self.assertIs(gold.summarize, summary_module.summarize)
        self.assertIs(focused.summarize, summary_module.summarize)

    def test_run_one_propagates_expected_identity_for_new_and_skipped_jobs(self):
        identity = self.identity()
        for state in ("new", "complete"):
            with self.subTest(state=state):
                def finish(*args, **kwargs):
                    self.write_result(identity)
                    return SimpleNamespace(returncode=0)

                with (
                    patch.object(gold, "inspect_contest_run", return_value=(state, identity)),
                    patch.object(gold.subprocess, "run", side_effect=finish) as process,
                ):
                    job = gold.run_one(
                        Path("current.json"), out_root=self.root, team_size=3,
                        max_turns=3, max_api_calls=9, system_variant="decentralized",
                    )
                self.assertEqual(job["run_identity"], identity)
                self.assertEqual(job["status"], "ok" if state == "new" else "skipped_complete")
                self.assertEqual(process.call_count, 1 if state == "new" else 0)
                row = self.rows(gold.summarize(
                    self.root, ["current"], run_results=[job],
                ))[0]
                self.assertEqual(row["task_utility"], "0.5")

    def test_verified_completion_and_skip_are_exported(self):
        for status in ("ok", "skipped_complete"):
            with self.subTest(status=status):
                identity = self.identity()
                self.write_result(identity)
                row = self.rows(gold.summarize(
                    self.root, ["current"], run_results=[self.job(identity, status)],
                ))[0]
                self.assertEqual(row["status"], "ok")
                self.assertEqual(row["batch_status"], status)
                self.assertEqual(row["competition_id"], "science_bowl")
                self.assertEqual(row["task_utility"], "0.5")
                self.assertEqual(row["run_fingerprint"], identity["fingerprint"])

    def test_result_replaced_after_job_validation_is_rejected(self):
        expected = self.identity()
        path = self.write_result(self.identity(model="old"))
        before = path.read_bytes()
        row = self.rows(gold.summarize(
            self.root, ["current"], run_results=[self.job(expected)],
        ))[0]
        self.assertEqual(row["status"], "invalid")
        self.assertIn("execution.model", row["reason"])
        self.assertEqual(row["score"], "")
        self.assertEqual(path.read_bytes(), before)

    def test_failed_job_and_missing_identity_never_contribute_scores(self):
        identity = self.identity()
        self.write_result(identity)
        for status in ("error", "blocked", "ok"):
            with self.subTest(status=status):
                job = {"problem_id": "current", "status": status}
                row = self.rows(gold.summarize(
                    self.root, ["current"], run_results=[job],
                ))[0]
                self.assertEqual(row["task_utility"], "")
                self.assertEqual(row["status"], "unverified" if status == "ok" else status)

    def test_completed_but_ungraded_is_not_a_failed_run(self):
        identity = self.identity()
        self.write_result(identity, self.result(identity, graded=False))
        row = self.rows(gold.summarize(
            self.root, ["current"], run_results=[self.job(identity)],
        ))[0]
        self.assertEqual(row["status"], "ungraded")
        self.assertEqual(row["batch_status"], "ok")
        self.assertEqual(row["task_utility"], "")
        self.assertEqual(row["turns_used"], "3")

    def test_corrupt_missing_and_incomplete_results_are_excluded(self):
        identity = self.identity()
        for value in ("not json", "[]", "null", "{}"):
            with self.subTest(value=value):
                path = self.write_result(identity)
                path.write_text(value, encoding="utf-8")
                row = self.rows(gold.summarize(
                    self.root, ["current"], run_results=[self.job(identity)],
                ))[0]
                self.assertEqual(row["status"], "invalid")
                self.assertEqual(row["task_utility"], "")
        path.unlink()
        row = self.rows(gold.summarize(
            self.root, ["current"], run_results=[self.job(identity)],
        ))[0]
        self.assertEqual(row["status"], "invalid")
        self.assertIn("new", row["reason"])

    def test_atomic_export_preserves_previous_summary_on_replace_failure(self):
        path = self.root / "summary.tsv"
        path.write_bytes(b"previous summary\n")
        with patch.object(summary_module.os, "replace", side_effect=PermissionError("locked")):
            with self.assertRaises(PermissionError):
                gold.summarize(self.root, [])
        self.assertEqual(path.read_bytes(), b"previous summary\n")
        self.assertFalse(list(self.root.glob(".summary-*.tmp")))

    def test_malformed_final_sections_do_not_crash_or_enter_summary(self):
        identity = self.identity()
        for section in ("grade", "metrics", "session_checkpoint", "budget", "timing"):
            with self.subTest(section=section):
                payload = self.result(identity)
                payload[section] = ["wrong shape"]
                self.write_result(identity, payload)
                row = self.rows(gold.summarize(
                    self.root, ["current"], run_results=[self.job(identity)],
                ))[0]
                self.assertEqual(row["status"], "invalid")
                self.assertEqual(row["score"], "")

    def test_batch_main_updates_pending_and_blocked_rows_without_old_scores(self):
        for batch in (gold, focused):
            with self.subTest(batch=batch.__name__):
                first, later = self.identity("current"), self.identity("later-job")
                self.write_result(first)
                old_path = self.write_result(self.identity("later-job", model="old"))
                before = old_path.read_bytes()
                manifests = []
                for name in ("current", "later-job"):
                    path = self.root / f"{name}.json"
                    path.write_text('{"competition_id":"science_bowl"}', encoding="utf-8")
                    manifests.append(path)

                def fake_run(manifest, **kwargs):
                    if manifest.stem == "current":
                        return self.job(first)
                    rows = self.rows(self.root / "summary.tsv")
                    self.assertEqual(rows[0]["task_utility"], "0.5")
                    self.assertEqual(rows[1]["status"], "pending")
                    self.assertEqual(rows[1]["task_utility"], "")
                    return {"problem_id": "later-job", "status": "blocked",
                            "reason": "identity mismatch"}

                with (
                    patch.object(sys, "argv", ["batch", "--output", str(self.root),
                                              "--competitions", "science_bowl"]),
                    patch.object(batch, "REPO_ROOT", self.root),
                    patch.object(batch, "write_manifests", return_value=manifests),
                    patch.object(batch, "run_one", side_effect=fake_run),
                    redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(batch.main(), 2)
                rows = self.rows(self.root / "summary.tsv")
                self.assertEqual(rows[1]["status"], "blocked")
                self.assertEqual(rows[1]["reason"], "identity mismatch")
                self.assertEqual(rows[1]["task_utility"], "")
                self.assertEqual(old_path.read_bytes(), before)

    def test_successful_batch_keeps_verified_scores_in_final_summary(self):
        identity = self.identity()
        self.write_result(identity)
        manifest = self.root / "current.json"
        manifest.write_text('{"competition_id":"science_bowl"}', encoding="utf-8")
        for batch in (gold, focused):
            for status in ("ok", "skipped_complete"):
                with (
                    self.subTest(batch=batch.__name__, status=status),
                    patch.object(sys, "argv", ["batch", "--output", str(self.root),
                                              "--competitions", "science_bowl"]),
                    patch.object(batch, "REPO_ROOT", self.root),
                    patch.object(batch, "write_manifests", return_value=[manifest]),
                    patch.object(batch, "run_one", return_value=self.job(identity, status)),
                    redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(batch.main(), 0)
                    row = self.rows(self.root / "summary.tsv")[0]
                    self.assertEqual(row["task_utility"], "0.5")
                    self.assertEqual(row["batch_status"], status)


if __name__ == "__main__":
    unittest.main()
