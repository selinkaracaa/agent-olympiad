import json
import sys
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import Mock, patch
from pypdf import PdfWriter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from artifact_contract import contract_for, delivery_route, ArtifactContract
from artifacts.contest_delivery import ArtifactRenderer, validate_source
from artifacts.assets import file_sha256
from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest
from llm import LLMResponse, LLMToolCall
from evaluation.models import load_rubric
from rules.loader import load_rule_card, DEFAULT_RULES_ROOT
from rules.storage import iter_rule_card_ids
from contest_config import BASELINE_NAMES, ContestRunConfig


class MockTeam:
    def __init__(self, source, approve=True, draft_action='work'):
        self.source, self.approve, self.requests = source, approve, []
        self.draft_action = draft_action
    def __call__(self, request):
        self.requests.append(request)
        if not request.tools:
            return LLMResponse('Coordinate, verify and reconcile.', 'mock', 'mock')
        names = {x['name'] for x in request.tools}
        marker = 'YOUR ELIGIBLE PENDING REVIEWS\n'
        pending = json.JSONDecoder().raw_decode(request.user_prompt.split(marker)[1])[0] if marker in request.user_prompt else []
        if pending and 'review_answer' in names:
            row = pending[0]
            name, args = 'review_answer', dict(problem_id=row['problem_id'],
                version_hash=row['version_hash'], content='Checked the source and rendered pages.',
                decision='approve' if self.approve else 'reject')
        elif self.draft_action in names and 'Agent_1' in request.system_prompt.split('\n')[0]:
            name, args = self.draft_action, {'content': self.source}
        elif 'submit' in names and len(names) == 1:
            name, args = 'submit', {}
        else:
            name, args = 'rest', {'reason': 'Awaiting reconciliation'}
        return LLMResponse('', 'mock', 'mock', tool_calls=(LLMToolCall(name, args),))


class ArtifactPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / 'task.pdf'
        writer = PdfWriter()
        writer.add_blank_page(width=720, height=540)
        with self.task.open('wb') as stream:
            writer.write(stream)

    def prepare(self, competition='wsc_writing'):
        return prepare_artifact_run(competition=competition, task_pdf=self.task,
            output=self.root / 'run', max_turns=2, provider='openai', model='mock',
            judge_model='mock-judge')

    def judge(self, prepared):
        rubric = load_rubric(prepared['rubric'])
        payload = {'criteria': [dict(id=c.id, score=c.min_score, max_score=c.max_score,
            evidence=['Synthetic fixture only'], justification='Mock judge response for plumbing test.',
            confidence=1, observable=c.observable) for c in rubric.criteria],
            'total_score': sum(c.min_score for c in rubric.criteria),
            'max_score': rubric.total_points, 'warnings': [], 'limitations': []}
        return Mock(return_value=LLMResponse(json.dumps(payload), 'mock', 'mock-judge'))

    def test_all_cards_configured_without_claiming_live_environment_support(self):
        ids = iter_rule_card_ids(DEFAULT_RULES_ROOT)
        benchmark_ids = {
            path.parent.name
            for path in (ROOT / "data" / "benchmarks").glob("*/benchmark.json")
        }
        self.assertEqual(set(ids), benchmark_ids)
        for name in ids:
            card = load_rule_card(name)
            ContestRunConfig('otc', card.team_size_default, card.simulation['max_turns'], rule_card=card)
        with self.assertRaises(ValueError):
            contract_for(load_rule_card('wro'))
        with self.assertRaises(ValueError):
            contract_for(load_rule_card('cfa_research_challenge'))

    def test_missing_rubric_fails_before_model_calls_or_output(self):
        with self.assertRaisesRegex(ValueError, 'no rubric'):
            self.prepare('gcch_harvard')
        self.assertFalse((self.root / 'run').exists())

    def test_security_rejects_active_network_and_local_html(self):
        for content in ('<script>alert(1)</script>', '<img src="file:///C:/secret">',
                        '<style>@import "https://example.com";</style>',
                        '<style>p{background:url(secret)}</style>', '<body onload="x()">',
                        '<p style="background:&#117;rl(file:///secret)">text</p>'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                validate_source(content, ArtifactContract('slides'))

    def test_document_runs_real_otc_renders_reviews_and_scores_same_pdf(self):
        prepared = self.prepare()
        team = MockTeam('A shared research note\n\nEvidence and reasoning for the supplied task.\nConclusion: verify assumptions.')
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=team, judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(file_sha256(Path(result['artifact']['pdf'])), result['artifact']['pdf_sha256'])
        self.assertEqual(judge.call_count, 1)
        coach = [r for r in team.requests if r.purpose == 'coach']
        self.assertEqual(len(coach), 1)
        self.assertFalse(coach[0].attachments)
        reviews = [r for r in team.requests if r.tools and 'Checked' not in r.system_prompt
                   and any(t['name'] == 'review_answer' for t in r.tools)
                   and len(r.attachments) == 2]
        self.assertTrue(reviews)
        for request in team.requests:
            self.assertNotIn('STRUCTURED RUBRIC:', request.user_prompt)
            self.assertNotIn('rubric_path', request.system_prompt)
        submission = judge.call_args.args[0].attachments[-1]
        self.assertEqual(file_sha256(submission.path), result['artifact']['pdf_sha256'])
        same = run_artifact_contest(prepared, agent_request=Mock(side_effect=AssertionError()),
                                    judge_request=Mock(side_effect=AssertionError()), resume=True)
        self.assertEqual(same['artifact'], result['artifact'])

    def test_all_five_baselines_share_rendering_and_judge_delivery(self):
        for variant in BASELINE_NAMES:
            with self.subTest(variant=variant):
                prepared = prepare_artifact_run(competition='wsc_writing', task_pdf=self.task,
                    output=self.root / variant, max_turns=2, provider='openai',
                    model='mock', judge_model='mock-judge', system_variant=variant)
                config = prepared['config']
                self.assertEqual(config.team_size == 1, variant == 'single_agent')
                team = MockTeam('Complete candidate for the writing task.', draft_action='render_pdf')
                judge = self.judge(prepared)
                def act(request):
                    response = team(request)
                    select = next((t for t in request.tools if t['name'] == 'select_problem'), None)
                    if select and response.tool_calls and response.tool_calls[0].name == 'rest':
                        choices = select['parameters']['properties']['problem_id'].get('enum') or ['deliverable']
                        return LLMResponse('', 'mock', 'mock', tool_calls=(
                            LLMToolCall('select_problem', {'problem_id': choices[0]}),))
                    return response
                result = run_artifact_contest(prepared, agent_request=act, judge_request=judge)
                self.assertEqual(result['status'], 'complete')
                self.assertEqual(file_sha256(judge.call_args.args[0].attachments[-1].path),
                                 result['artifact']['pdf_sha256'])
                contest = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
                self.assertEqual(contest['modules'], config.modules.as_dict())
                self.assertTrue(any(e['kind'] == 'render_pdf' for e in contest['memory']['events']))
                self.assertEqual(sum(r.purpose == 'coach' for r in team.requests), int(config.modules.coach))
                if not config.modules.coach:
                    self.assertTrue(all('BASIC OTC' not in r.system_prompt for r in team.requests))

    def test_rejected_document_is_collected_and_judged_at_deadline(self):
        prepared = self.prepare()
        self.assertIsNone(prepared['config'].max_api_calls)
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=MockTeam('Complete draft.', False),
                                      judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(judge.call_count, 1)
        contest = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
        self.assertTrue(any(r['decision'] == 'reject' for r in contest['session_checkpoint']['tasks'][0]['reviews']))
        collected = next(e for e in contest['memory']['events'] if e['kind'] == 'deadline_drafts_submitted')
        self.assertTrue(collected['payload']['review_gate_waived'])
        self.assertEqual(Path(result['artifact']['source']).read_text(encoding='utf-8'), 'Complete draft.')

    def test_explicit_render_pdf_records_reviewed_version_and_exact_judged_pdf(self):
        prepared = self.prepare()
        team = MockTeam('Explicit PDF tool\n\nComplete candidate and evidence.', draft_action='render_pdf')
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=team, judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertTrue(result['artifact']['previews'])
        contest = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
        self.assertTrue(any(e['kind'] == 'render_pdf' for e in contest['memory']['events']))
        self.assertEqual(file_sha256(judge.call_args.args[0].attachments[-1].path), result['artifact']['pdf_sha256'])

    def test_rejected_explicit_pdf_is_submitted_at_deadline(self):
        prepared = self.prepare()
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared,
            agent_request=MockTeam('Rejected explicit candidate.', approve=False, draft_action='render_pdf'),
            judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(judge.call_count, 1)
        self.assertEqual(file_sha256(judge.call_args.args[0].attachments[-1].path), result['artifact']['pdf_sha256'])

    def test_unreviewed_slides_are_collected_and_rendered_for_judging(self):
        prepared = self.prepare('ieo_business_case')
        source = '<html><body><section><h1>Final candidate</h1><p>Evidence and proposal.</p></section></body></html>'
        team = MockTeam(source)
        def without_review(request):
            response = team(request)
            if response.tool_calls and response.tool_calls[0].name == 'review_answer':
                return LLMResponse('', 'mock', 'mock', tool_calls=(LLMToolCall('rest', {'reason': 'No review completed'}),))
            return response
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=without_review, judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        contest = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
        self.assertEqual(contest['session_checkpoint']['tasks'][0]['reviews'], [])
        self.assertEqual(Path(result['artifact']['source']).read_text(encoding='utf-8'), source)
        self.assertEqual(judge.call_count, 1)

    def test_slide_candidate_is_html_then_pdf_and_reviewed_before_grading(self):
        prepared = self.prepare('ieo_business_case')
        html = '<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:Arial}h1{font-size:42px}</style></head><body><section><h1>Delivery fixture</h1><p>Evidence and proposal.</p></section></body></html>'
        team, judge = MockTeam(html), self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=team, judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['artifact']['pages'], 1)
        self.assertEqual(Path(result['artifact']['source']).read_text(encoding='utf-8'), html)

    def test_changed_rubric_or_task_blocks_resume(self):
        prepared = self.prepare()
        team = MockTeam('Complete draft.')
        run_artifact_contest(prepared, agent_request=team, judge_request=self.judge(prepared))
        changed = dict(prepared, identity=dict(prepared['identity']))
        changed['identity']['settings'] = dict(prepared['identity']['settings'], extra='changed')
        from contest_run_identity import content_hash
        changed['identity']['fingerprint'] = content_hash(changed['identity']['settings'])
        with self.assertRaises(ValueError):
            run_artifact_contest(changed, agent_request=Mock(), judge_request=Mock(), resume=True)

    def test_tampered_pdf_is_not_silently_reused(self):
        renderer = ArtifactRenderer(self.root / 'versions', ArtifactContract('document'))
        receipt = renderer(None, 'render_pdf', {'content': 'Version one'})
        Path(receipt['pdf']).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            renderer(None, 'render_pdf', {'content': 'Version one'})

    def test_judge_failure_resumes_without_rerunning_team(self):
        prepared = self.prepare()
        with self.assertRaisesRegex(RuntimeError, 'judge unavailable'):
            run_artifact_contest(prepared, agent_request=MockTeam('Approved complete draft.'),
                                 judge_request=Mock(side_effect=RuntimeError('judge unavailable')))
        result = run_artifact_contest(prepared, resume=True,
            agent_request=Mock(side_effect=AssertionError('Team must not run twice')),
            judge_request=self.judge(prepared))
        self.assertEqual(result['status'], 'complete')

    def test_oversized_source_is_not_silently_truncated_and_scored(self):
        prepared = self.prepare()
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared,
            agent_request=MockTeam('x' * 60001), judge_request=judge)
        self.assertEqual(result['status'], 'unsubmitted')
        judge.assert_not_called()

    def test_legacy_entry_delegates_to_canonical_runner(self):
        import run_presentation_artifact as legacy
        with patch.object(legacy, 'run_otc', return_value=0) as runner:
            legacy.main(['--competition', 'ieo_business_case', '--task-pdf', str(self.task),
                         '--rounds', '4', '--prepare-only'])
        argv = runner.call_args.args[0]
        self.assertIn('--prepare-only', argv)
        self.assertEqual(argv[argv.index('--max-turns') + 1], '4')


if __name__ == '__main__':
    unittest.main()
