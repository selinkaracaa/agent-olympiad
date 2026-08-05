from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.leaderboard import Leaderboard, build_leaderboard
from pipeline.llm import build_agent_attachments, mock_query, mock_request
from pipeline.loader import load_packet, load_rules
from pipeline.models import BenchmarkProblem, RuleCard
from pipeline.orchestrator import run_problem
from pipeline.rule_block import RuleBlock
from pipeline.scorers import score_submission
from pipeline.src_bridge import REPO_ROOT
from pipeline.team import form_team


class PipelinePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = load_packet("iol_team", "iol_team_2008")

    def test_loader_uses_official_team_and_agent_visible_pdf(self):
        self.assertEqual(self.packet.problem.team_size, 4)
        paths = {asset.path.name for asset in self.packet.problem.assets}
        self.assertIn("iol-2008-team-prob.en.pdf", paths)
        self.assertNotIn("iol-2008-team-sol.en.pdf", paths)
        with tempfile.TemporaryDirectory() as temp_dir:
            attachments = build_agent_attachments(
                self.packet.problem.assets,
                media="pdf",
                work_dir=Path(temp_dir),
            )
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].mime_type, "application/pdf")

    def test_official_team_is_default_and_override_is_explicit(self):
        team = form_team(self.packet.problem, self.packet.rules)
        self.assertEqual(team.actual_team_size, 4)
        self.assertTrue(team.officially_comparable)
        with self.assertRaises(ValueError):
            form_team(self.packet.problem, self.packet.rules, 2)
        experimental = form_team(
            self.packet.problem,
            self.packet.rules,
            2,
            allow_noncomparable=True,
        )
        self.assertFalse(experimental.officially_comparable)

    def test_unimplemented_advertised_tool_fails_closed(self):
        raw = dict(self.packet.rules.raw)
        raw["allowed_tools"] = ["execute_code"]
        rules = RuleCard.from_dict(raw, competition_id="iol_team")
        packet = type(self.packet)(
            competition_id=self.packet.competition_id,
            problem=self.packet.problem,
            rules=rules,
        )
        with self.assertRaises(ValueError):
            RuleBlock(
                packet=packet,
                leaderboard=Leaderboard.simulated("test", [90]),
            )


class PipelineEvaluationTests(unittest.TestCase):
    def test_scalar_gold_uses_canonical_gold_evaluator(self):
        problem = BenchmarkProblem.from_dict(
            {
                "problem_id": "demo_q1",
                "competition_id": "demo",
                "task_type": "numerical_sheet",
                "problem_description": "Answer the question.",
                "team_size": 2,
                "gold_label": {"expected_answer": ["42", "forty-two"]},
                "evaluation": {"evaluator_id": "gold_answer_v1"},
                "total_points": 5,
            },
            competition_id="demo",
            repository_root=REPO_ROOT,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            score = score_submission(
                problem,
                "42",
                mock_request,
                work_dir=Path(temp_dir),
            )
        self.assertEqual(score.method, "gold_answer_v1")
        self.assertEqual(score.raw_score, 5)
        self.assertEqual(score.normalized_100, 100)

    def test_mock_run_uses_registry_evaluator(self):
        packet = load_packet("iol_team", "iol_team_2008")
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_problem(
                packet,
                mock_query,
                mock_request,
                build_leaderboard(load_rules("iol_team")),
                rounds=1,
                media="text",
                work_dir=Path(temp_dir),
            )
        self.assertEqual(result["score"]["method"], "rubric_llm_v1")
        self.assertEqual(result["score"]["normalized_100"], 62.0)
        self.assertTrue(result["team"]["officially_comparable"])

    def test_codeforces_scale_is_not_ranked_against_normalized_score(self):
        board = Leaderboard(
            competition_name="Codeforces demo",
            entries=[{"name": "tourist", "score": 2400.0, "source": "codeforces"}],
            scale_id="codeforces_points",
            comparison_status="not_comparable",
        )
        snapshot = board.update(
            80,
            "demo",
            score_scale_id="normalized_100",
            evaluator_id="rubric_llm_v1",
        )
        self.assertEqual(snapshot["comparison_status"], "not_comparable")
        self.assertNotIn("rank", snapshot)
        self.assertEqual(snapshot["top"][0]["name"], "tourist")


if __name__ == "__main__":
    unittest.main()
