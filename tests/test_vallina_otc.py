import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from pypdf import PdfWriter
from contest_config import BASELINES, ContestRunConfig, canonical_baseline
from contest_manifest import ContestManifest, ManifestTask
from contest_policy import _resolved_actions
from contest_runner import run_contest
from contest_run_identity import build_run_identity, validate_run_identity
from rules.loader import load_rule_card, DEFAULT_RULES_ROOT
from rules.storage import iter_rule_card_ids
from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest
from test_otc_artifact_pipeline import MockTeam
from evaluation.models import load_rubric
from llm import LLMResponse


class VallinaOTCTests(unittest.TestCase):
    def config(self, name='vallina_otc', turns=3):
        card = load_rule_card('arml_local')
        return ContestRunConfig(name, card.team_size_default, turns, rule_card=card)

    def manifest(self):
        return ContestManifest('basic-test', 'arml_local', (
            ManifestTask('q1', 'q1', None, 'TASK_SECRET What is 2+2?', 'math', 1, False, {}),
            ManifestTask('q2', 'q2', None, 'What is 3+3?', 'math', 1, False, {}),
        ))

    def test_presets_and_aliases_are_separate(self):
        self.assertEqual(canonical_baseline('vanilla'), 'decentralized')
        self.assertEqual(canonical_baseline('vanilla_otc'), 'vallina_otc')
        self.assertTrue(self.config().features.basic_open_table)
        self.assertFalse(self.config().review_required)
        self.assertTrue(self.config('otc').review_required)
        self.assertTrue(BASELINES['otc'].memory_actions)
        with self.assertRaises(ValueError):
            ContestRunConfig('vallina_otc', 3, 3, rule_card=load_rule_card('wsc_writing'), require_review=True)
        with self.assertRaises(ValueError):
            ContestRunConfig('otc', 3, 3, rule_card=load_rule_card('wsc_writing'),
                             features=BASELINES['vallina_otc'])

    def test_tools_and_card_immutability(self):
        config = self.config()
        names = {s.name for s in _resolved_actions(self.manifest(), config)}
        self.assertTrue({'work', 'speak', 'rest', 'submit'} <= names)
        self.assertFalse(names & {'remember', 'retrieve_memory', 'share_note', 'review_answer',
                                  'request_review', 'propose', 'challenge', 'provide_evidence',
                                  'revise', 'decide', 'direct_message'})
        self.assertTrue(config.rule_card.simulation['open_table_coach']['review_required'])
        self.assertFalse(config.otc_policy.structured_deliberation)
        self.assertFalse(config.otc_policy.discussion.report_after_work)

    def test_deadline_collects_unreviewed_draft_and_coach_blind_once(self):
        requests = []
        def query(system, user):
            requests.append((system, user))
            if system.startswith('You are Coach'):
                self.assertNotIn('TASK_SECRET', user)
                self.assertIn('"review_required": false', user)
                return 'Discuss freely and respect contest rules.'
            return 'CURRENT_THOUGHT_' + str(len(requests))
        team = MockTeam('4')
        result = run_contest(self.manifest(), query, self.config(turns=1),
                             action_request_fn=team, action_transport='native')
        self.assertEqual(sum(s.startswith('You are Coach') for s,u in requests), 1)
        self.assertIn('4', result['submissions'].values())
        for request in team.requests:
            self.assertNotIn('Mandatory review:', request.system_prompt)
            self.assertNotIn('SHARED ANSWER REVIEW HISTORY', request.user_prompt)

    def test_identity_blocks_cross_baseline_resume(self):
        basic = build_run_identity(self.manifest(), self.config(), execution={}, evaluation={})
        full = build_run_identity(self.manifest(), self.config('otc'), execution={}, evaluation={})
        with self.assertRaises(ValueError):
            validate_run_identity(full, basic, artifact='checkpoint')

    def test_all_cards_keep_resource_and_submission_rules(self):
        for name in iter_rule_card_ids(DEFAULT_RULES_ROOT):
            card = load_rule_card(name)
            base = ContestRunConfig('vallina_otc', card.team_size_default, 3, rule_card=card)
            full = ContestRunConfig('otc', card.team_size_default, 3, rule_card=card)
            for field in ('communication', 'submitters', 'workstation_lease',
                          'run_judging_latency_turns', 'max_chars_by_action',
                          'private_think_calls_per_turn'):
                self.assertEqual(getattr(base.otc_policy, field), getattr(full.otc_policy, field), (name, field))

    def test_previous_private_thoughts_are_not_reinjected(self):
        seen = []
        def query(system, user):
            if system.startswith('You are Coach'):
                return 'Respect rules.'
            self.assertNotIn('PRIVATE_CANARY_', user)
            seen.append(user)
            return 'PRIVATE_CANARY_' + str(len(seen))
        # No work or submission; exercise several consecutive turns.
        def action(request):
            from llm import LLMToolCall
            return LLMResponse('', 'mock', 'mock', tool_calls=(LLMToolCall('rest', {'reason': 'Wait'}),))
        run_contest(self.manifest(), query, self.config(turns=3), action_request_fn=action,
                    action_transport='native')
        self.assertGreater(len(seen), self.config().team_size)

    def test_artifact_without_peer_approval_still_renders_and_judges(self):
        self.check_artifact('wsc_writing', 'Complete unreviewed essay.')

    def test_slides_without_peer_approval_still_render_and_judge(self):
        self.check_artifact('ieo_business_case',
            '<html><body><section><h1>Proposal</h1><p>Evidence and conclusion.</p></section></body></html>')

    def test_unsafe_slides_do_not_reach_judge(self):
        self.check_artifact('ieo_business_case', '<script>alert(1)</script>', valid=False)

    def check_artifact(self, competition, source, valid=True):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / 'task.pdf'
            writer = PdfWriter()
            writer.add_blank_page(width=600, height=800)
            with pdf.open('wb') as stream:
                writer.write(stream)
            p = prepare_artifact_run(competition=competition, task_pdf=pdf,
                output=root / 'run', max_turns=3, provider='openai', model='mock',
                system_variant='vallina_otc')
            rubric = load_rubric(p['rubric'])
            payload = dict(criteria=[dict(id=c.id, score=0, max_score=c.max_score,
                evidence=['Fixture'], justification='Synthetic test only.', confidence=1,
                observable=c.observable) for c in rubric.criteria], total_score=0,
                max_score=rubric.total_points, warnings=[], limitations=[])
            judge = Mock(return_value=LLMResponse(json.dumps(payload), 'mock', 'mock'))
            result = run_artifact_contest(p, agent_request=MockTeam(source), judge_request=judge)
            if not valid:
                self.assertEqual(result['status'], 'unsubmitted')
                judge.assert_not_called()
                return
            self.assertEqual(result['status'], 'complete')
            self.assertTrue(Path(result['artifact']['pdf']).is_file())
            saved = json.loads(Path(result['contest_file']).read_text())
            self.assertEqual(saved['session_checkpoint']['tasks'][0]['reviews'], [])
            judge.assert_called_once()


if __name__ == '__main__':
    unittest.main()
