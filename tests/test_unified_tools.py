"""Canonical tool permissions and real PDF execution across both runtimes."""
import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import Mock, patch

from pypdf import PdfReader
from action_modules.task_specific import resolve_contest_interface
from actions import parse_typed_action
from action_wire import normalize_invocation
from artifact_contract import ArtifactContract
from artifacts.assets import file_sha256
from artifacts.contest_delivery import ArtifactRenderer
from contest_adapters import EnvironmentTaskExecutor
from contest_actions import _apply_action
from contest_config import ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from env import OlympiadEnvironment, TOOL_ACTIONS
from rules.loader import DEFAULT_RULES_ROOT, load_rule_card
from rules.storage import iter_rule_card_ids
from tool_registry import (ACTION_REGISTRY, COMMON_ACTION_NAMES, COMMON_TOOL_NAMES,
                           SPECIFIC_TOOL_NAMES, TOOL_ACTION_NAMES,
                           competition_permissions, resolve_action_names)


class UnifiedToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, competition, *, fixtures=None):
        programming = competition in {'icpc', 'iiot', 'codeforces'}
        kind = 'programming' if programming else 'general'
        card = load_rule_card(competition)
        row = dict(problem_id='test', task_type=kind,
                   problem_description='Public test task.', team_size=card.team_size_default,
                   tool_fixtures=fixtures or {})
        directory = self.root / competition
        directory.mkdir(exist_ok=True)
        (directory / 'benchmark.json').write_text(json.dumps([row]), encoding='utf-8')
        task = ManifestTask('test', 'test', None, row['problem_description'], kind, 1, programming, row)
        return ContestManifest('test-run', competition, (task,))

    def test_ownership_execution_and_permission_are_independent(self):
        self.assertEqual(COMMON_TOOL_NAMES, {'use_calculator', 'web_search', 'execute_code', 'render_pdf'})
        self.assertEqual(SPECIFIC_TOOL_NAMES, {'read_lab_equipment', 'read_star_chart'})
        self.assertEqual(TOOL_ACTION_NAMES, TOOL_ACTIONS)
        self.assertFalse(ACTION_REGISTRY['submit_code'].is_tool)
        self.assertTrue(ACTION_REGISTRY['submit_code'].submission)
        self.assertTrue(replace(ACTION_REGISTRY['execute_code'], module='task_specific').is_tool)
        self.assertTrue(COMMON_TOOL_NAMES <= COMMON_ACTION_NAMES)
        self.assertFalse(TOOL_ACTION_NAMES & resolve_action_names('arml_local'))

    def test_all_rule_cards_resolve_same_tools_in_both_runtimes(self):
        for name in iter_rule_card_ids(DEFAULT_RULES_ROOT):
            with self.subTest(competition=name):
                manifest = self.fixture(name)
                interface = resolve_contest_interface(manifest)
                expected = {s.name for s in interface.actions if s.is_tool}
                for mode in ('off', 'enforced'):
                    env = OlympiadEnvironment(name, 'test', base_path=str(self.root), rules_mode=mode)
                    self.assertEqual(set(env.get_available_tools()), expected, mode)
                    self.assertNotIn('query_rules', env.unavailable_declared_tools)

    def test_no_legacy_permission_names_and_no_implicit_solver_access(self):
        for name in ('mcm', 'icm', 'iypt', 'itym'):
            permitted = competition_permissions(name)
            self.assertTrue({'execute_code', 'render_pdf', 'work'} <= permitted)
            self.assertFalse({'code_execution', 'document_authoring', 'slide_authoring'} & permitted)
        self.assertNotIn('web_search', resolve_action_names('fyziklani'))
        empty = replace(load_rule_card('icpc'), allowed_tools=())
        self.assertEqual(competition_permissions('icpc', rule_card=empty), set())
        self.assertNotIn('read_lab_equipment', resolve_action_names(
            'ijso_practical', declared_capabilities={'read_lab_equipment'}))

    def test_pdf_text_and_native_invocations_share_validation(self):
        content = 'A | B\nSecond line.'
        specs = [ACTION_REGISTRY['render_pdf']]
        parsed = parse_typed_action(json.dumps({'action': 'render_pdf', 'arguments': {'content': content}}), specs)
        self.assertEqual(parsed, ('render_pdf', {'content': content}, None))
        text = normalize_invocation('render_pdf', content)
        self.assertTrue(text.ok)
        self.assertEqual(text.arguments, {'content': content})
        self.assertFalse(normalize_invocation('render_artifact', content).ok)
        self.assertFalse(normalize_invocation('code_execution', 'print(42)').ok)

    def test_environment_and_session_adapter_return_real_pdf_and_previews(self):
        manifest = self.fixture('wsc_writing')
        executor = EnvironmentTaskExecutor(manifest, benchmark_root=str(self.root))
        env = executor._environment(manifest.tasks[0])
        env._pdf_renderer = ArtifactRenderer(self.root / 'versions', ArtifactContract('document'))
        source = 'A verified document\n\nThe experiment has 43 competition tracks.\n中文摘要：统一工具接口。'
        receipt = executor(manifest.tasks[0], 'render_pdf', {'content': source})
        self.assertTrue(receipt['valid'])
        self.assertEqual(receipt['pdf_sha256'], file_sha256(Path(receipt['pdf'])))
        self.assertIn('43 competition tracks', ''.join(p.extract_text() for p in PdfReader(receipt['pdf']).pages))
        self.assertIn('中文摘要', ''.join(p.extract_text() for p in PdfReader(receipt['pdf']).pages))
        self.assertEqual(len(receipt['previews']), receipt['pages'])
        for preview in receipt['previews']:
            path = Path(preview['path'])
            self.assertTrue(path.read_bytes().startswith(b'\x89PNG'))
            self.assertEqual(file_sha256(path), preview['sha256'])
        same = json.loads(env.execute_action('Agent_1', 'render_pdf', {'content': source}))
        self.assertEqual(same, receipt)
        self.assertEqual(env.workspace['final_answer'], '')

    def test_pdf_permission_gate_prevents_render_side_effects(self):
        self.fixture('arml_local')
        env = OlympiadEnvironment('arml_local', 'test', base_path=str(self.root))
        env._pdf_renderer = Mock(side_effect=AssertionError('renderer must not run'))
        result = env.execute_action('Agent_1', 'render_pdf', {'content': 'Forbidden PDF'})
        self.assertTrue(result.startswith('RULE VIOLATION'))
        env._pdf_renderer.assert_not_called()

    def test_artifact_solver_tools_share_backend_without_overwriting_pdf_candidate(self):
        manifest = replace(self.fixture('mcm'), metadata={'artifact_contract': asdict(ArtifactContract('document'))})
        renderer = ArtifactRenderer(self.root / 'versions', ArtifactContract('document'))
        executor = EnvironmentTaskExecutor(manifest, benchmark_root=self.root,
                                          renderer=renderer, rule_card=load_rule_card('mcm'))
        session = ContestSession([TaskUnit('test', kind='non_programming')], ContestBudgetState(max_turns=5))
        session.select_task('test')
        memory = ContestMemory(run_id='r', session_id='test-run', competition_id='mcm')
        kwargs = dict(agent='Agent_1', manifest=manifest, session=session, memory=memory,
                      config=ContestRunConfig('decentralized', 2, 5), strategic_policy=None,
                      task_action_executor=executor)
        _apply_action(action='render_pdf', arguments={'content': 'The modeling report.'}, **kwargs)
        version = session.active_task.versions[-1]
        env = executor._environment(manifest.tasks[0])
        with patch.object(env, '_run_code', return_value='Execution output: 42') as code:
            _apply_action(action='execute_code', arguments={'code': 'print(42)'}, **kwargs)
            code.assert_called_once_with('print(42)')
        self.assertEqual(session.active_task.versions, [version])
        self.assertTrue(any(e.kind == 'execute_code_result' for e in memory.view('Agent_1')))
        calc = executor(manifest.tasks[0], 'use_calculator', {'expression': '6*7'})
        self.assertTrue(calc['valid'])
        self.assertIn('42', calc['result'])
        self.assertEqual(renderer.latest['source_sha256'], file_sha256(Path(renderer.latest['source'])))

    def test_card_search_permission_reaches_backend_without_stale_audit_denial(self):
        self.fixture('cfa_research_challenge')
        env = OlympiadEnvironment('cfa_research_challenge', 'test', base_path=str(self.root))
        with patch('env.live_web_search', return_value='Public evidence') as search:
            value = env.execute_action('Agent_1', 'web_search', {'query': 'public annual report'})
        search.assert_called_once_with('public annual report')
        self.assertIn('Public evidence', value)

    def test_render_failure_and_tampering_never_reuse_success(self):
        renderer = ArtifactRenderer(self.root / 'versions', ArtifactContract('document', max_source_chars=100))
        first = renderer(None, 'render_pdf', {'content': 'Verified candidate.'})
        with self.assertRaises(ValueError):
            renderer(None, 'render_pdf', {'content': 'x' * 101})
        self.assertEqual(renderer.latest, first)
        changed = ArtifactRenderer(self.root / 'versions', ArtifactContract('document', max_source_chars=90))
        with self.assertRaisesRegex(ValueError, 'contract mismatch'):
            changed(None, 'render_pdf', {'content': 'Verified candidate.'})
        Path(first['previews'][0]['path']).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'preview/hash mismatch'):
            renderer(None, 'render_pdf', {'content': 'Verified candidate.'})


if __name__ == '__main__':
    unittest.main()
