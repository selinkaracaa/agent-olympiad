from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_manifest import ContestManifest, load_contest_manifest  # noqa: E402
from run_contest_smoke import run_pair  # noqa: E402


class ContestMatchedSmokeTests(unittest.TestCase):
    def test_latest_otc_and_vanilla_keep_matched_resources(self) -> None:
        full = load_contest_manifest(
            REPO_ROOT / "data" / "contest_manifests" / "icpc_wf_2012_5.json",
            benchmark_root=REPO_ROOT / "data" / "benchmarks",
        )
        manifest = ContestManifest(
            session_id="icpc-two-smoke",
            competition_id=full.competition_id,
            tasks=full.tasks[:2],
        )
        pair = run_pair(
            manifest,
            max_turns=10,
            max_api_calls=30,
            max_tokens=10000,
        )
        vanilla = pair["results"]["decentralized"]
        strategic = pair["results"]["otc"]

        self.assertEqual(strategic["baseline"]["coach"], "card")
        self.assertEqual(vanilla["baseline"]["coach"], "none")
        self.assertFalse(vanilla["baseline"]["memory_actions"])
        self.assertEqual(
            vanilla["budget"]["max_api_calls"],
            strategic["budget"]["max_api_calls"],
        )
        for result in (vanilla, strategic):
            self.assertLessEqual(result["budget"]["api_calls_used"], 30)
            self.assertFalse([e for e in result["memory"]["events"] if e["kind"] == "action_error"])
        kinds = {e["kind"] for e in strategic["memory"]["events"]}
        self.assertIn("think", kinds)
        self.assertNotIn("coach_opening_summary", kinds)
        self.assertEqual(strategic["diagnostics"]["otc"]["coach_calls"], 1)


if __name__ == "__main__":
    unittest.main()
