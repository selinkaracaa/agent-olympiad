"""The contest clock ends play; every available candidate gets a final attempt."""
import tempfile
import unittest
from pathlib import Path

from contest_config import ContestRunConfig
from contest_runner import run_contest
from run_competition_batch import inspect_contest_run
from test_otc_rulecard import ARML, ICPC, ScriptedLLM, action, arml_manifest, icpc_manifest
from llm import LLMResponse, LLMToolCall


class DeadlinePolicyTests(unittest.TestCase):
    def test_sixty_turns_finish_despite_extra_action_repair_calls(self):
        def model(request):
            calls = (LLMToolCall('rest', {'reason': 'Continue contest'}),)
            if 'ACTION RESPONSE REJECTED' not in request.user_prompt:
                calls += (LLMToolCall('check_budget', {}),)
            return LLMResponse('', 'mock', 'mock', tool_calls=calls)
        result = run_contest(arml_manifest(), ScriptedLLM({}),
            ContestRunConfig('otc', 6, 60, rule_card=ARML), action_request_fn=model)
        self.assertEqual(result['budget']['turns_used'], 60)
        self.assertIsNone(result['budget']['max_api_calls'])
        self.assertGreater(result['budget']['api_calls_used'], 60 * 6 * 2 + 1)
        self.assertFalse(any(e['kind'] == 'action_error' for e in result['memory']['events']))

    def test_otc_cli_has_no_implicit_api_limit(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as output:
            state, identity = inspect_contest_run([
                '--contest-manifest', str(root / 'data/contest_manifests/icpc_wf_2012.json'),
                '--system-variant', 'otc', '--max-turns', '60', '--output', output,
            ])
        self.assertEqual(state, 'new')
        self.assertEqual(identity['settings']['config']['max_turns'], 60)
        self.assertIsNone(identity['settings']['config']['max_api_calls'])

    def test_otc_deadline_attempts_sample_failure_without_independent_approval_by_default(self):
        scripts = ScriptedLLM({'Agent_1': [action('execute_code', code='print(7)')]})
        calls = []
        def executor(task, name, arguments):
            calls.append((task.task_id, name, arguments))
            return {'valid': True, 'sample_verdict': 'WA', 'verdict': 'AC'}
        result = run_contest(icpc_manifest(), scripts,
            ContestRunConfig('otc', 3, 1, rule_card=ICPC), task_action_executor=executor)
        self.assertEqual([row[:2] for row in calls], [('p1', 'execute_code'), ('p1', 'submit_code')])
        self.assertTrue(result['review_required'])
        task = result['session_checkpoint']['tasks'][0]
        self.assertFalse(task['reviews'])
        self.assertFalse(task['versions'][-1]['evidence_refs'])
        self.assertEqual(result['tasks']['p1']['terminal_verdict'], 'AC')
        intent = next(e for e in result['memory']['events'] if e['kind'] == 'programming_deadline_submit_started')
        self.assertTrue(intent['payload']['review_gate_waived'])
        self.assertTrue(intent['payload']['sample_gate_waived'])


if __name__ == '__main__':
    unittest.main()
