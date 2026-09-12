"""Contracts shared by the vanilla baseline and strategic contest system."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from contest_manifest import ContestManifest, ManifestTask, load_contest_manifest
from contest_adapters import grade_contest_result
from contest_feature_fixtures import review_ablation_config
from contest_runner import ContestRunConfig, _resolved_actions, _scheduled_agent_task, _actions_for_agent, run_contest
from contest_session import ContestSession, ContestBudgetState, TaskUnit


def task(name, gold=None, competition_type='team_contest'):
    return ManifestTask(name, name, None, f'Solve {name}', competition_type, 1, False, {'gold_label': gold or {}})


class ProtocolRegressionTests(unittest.TestCase):
    def test_vanilla_excludes_review_workflow_actions(self):
        m=ContestManifest('paired','arml_local',(task('q1'),task('q2')))
        s=ContestSession([TaskUnit('q1',kind='non_programming'),TaskUnit('q2',kind='non_programming')],ContestBudgetState(max_turns=5))
        actions=_actions_for_agent(_resolved_actions(m),s,ContestRunConfig('vanilla',3,5),'Agent_1',answer_sheet_contest=True)
        self.assertNotIn('request_review',{a.name for a in actions})
        self.assertNotIn('review_answer',{a.name for a in actions})

    def test_duplicate_answer_is_a_noop_and_preserves_review(self):
        s=ContestSession([TaskUnit('q1',kind='non_programming')],ContestBudgetState(max_turns=5))
        s.select_task('q1')
        first=s.create_answer('Final answer: 42',author='Agent_1')
        review=s.record_task_review('q1','Agent_2','checked',version_hash=first.version_hash)
        duplicate=s.create_answer('Final answer: 42',author='Agent_3')
        self.assertIs(duplicate,first)
        self.assertEqual(len(s.task('q1').versions),1)
        self.assertFalse(review.stale)

    def test_vanilla_moves_to_next_unseen_after_recording_a_draft(self):
        m=ContestManifest('paired','arml_local',(task('q1'),task('q2')))
        prompts=[]
        responses=iter([
            '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
            '{"action":"work","arguments":{"content":"Final answer: 11"}}',
            '{"action":"work","arguments":{"content":"Final answer: 22"}}',
        ])
        def query(_system,user):
            prompts.append(user)
            return next(responses)
        result=run_contest(m,query,ContestRunConfig('vanilla',1,3,stall_turns=2))
        self.assertIn('ACTIVE TASK q2',prompts[2])
        self.assertEqual(result['submissions'],{'q1':'Final answer: 11','q2':'Final answer: 22'})
        self.assertEqual(result['diagnostics']['baseline_mechanical_switches'],1)

    def test_vanilla_stall_guard_moves_to_an_unseen_task(self):
        m=ContestManifest('paired','arml_local',(task('q1'),task('q2')))
        prompts=[]
        responses=iter([
            '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
            '{"action":"rest","arguments":{"reason":"stuck"}}',
            '{"action":"rest","arguments":{"reason":"stuck"}}',
            '{"action":"work","arguments":{"content":"Final answer: 22"}}',
        ])
        def query(_system,user):
            prompts.append(user)
            return next(responses)
        result=run_contest(m,query,ContestRunConfig('vanilla',1,4,stall_turns=2))
        self.assertIn('ACTIVE TASK q2',prompts[3])
        self.assertEqual(result['submissions']['q2'],'Final answer: 22')
        self.assertGreaterEqual(result['diagnostics']['baseline_mechanical_switches'],1)

    def test_incomplete_sheet_submission_is_hidden_for_both_variants(self):
        m=ContestManifest('paired','arml_local',(task('q1'),task('q2')))
        s=ContestSession([TaskUnit('q1',kind='non_programming'),TaskUnit('q2',kind='non_programming')],ContestBudgetState(max_turns=5))
        s.select_task('q1'); s.create_answer('42',author='Agent_1')
        for variant in ('vanilla','strategic'):
            with self.subTest(variant=variant):
                actions=_actions_for_agent(_resolved_actions(m),s,(review_ablation_config(3,5) if variant == "strategic" else ContestRunConfig(variant,3,5)),'Agent_2',answer_sheet_contest=True)
                self.assertNotIn('submit',{a.name for a in actions})

    def test_complete_vanilla_sheet_exposes_only_submit(self):
        m=ContestManifest('paired','arml_local',(task('q1'),task('q2')))
        s=ContestSession([TaskUnit('q1',kind='non_programming'),TaskUnit('q2',kind='non_programming')],ContestBudgetState(max_turns=5))
        s.select_task('q1'); s.create_answer('11',author='Agent_1')
        s.select_task('q2'); s.create_answer('22',author='Agent_2')
        actions=_actions_for_agent(_resolved_actions(m),s,ContestRunConfig('vanilla',3,5),'Agent_3',answer_sheet_contest=True)
        self.assertEqual({a.name for a in actions},{'submit'})

    def test_both_variants_hand_in_drafts_on_budget_expiry(self):
        m = ContestManifest('paired', 'arml_local', (task('q1'), task('q2')))
        for variant in ('vanilla', 'strategic'):
            with self.subTest(variant=variant):
                responses = iter([
                    '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                    '{"action":"work","arguments":{"content":"Final answer: 42"}}',
                ])
                result = run_contest(m, lambda *_: next(responses), (review_ablation_config(1, 2) if variant == "strategic" else ContestRunConfig(variant, 1, 2)))
                self.assertEqual(result['submissions']['q1'], 'Final answer: 42')
                self.assertEqual(result['submissions']['q2'], '')
                self.assertTrue(result['diagnostics']['deadline_submission'])

    def test_nonprogramming_review_only_assignment_is_scheduled(self):
        s = ContestSession([TaskUnit('q1', kind='non_programming'), TaskUnit('q2', kind='non_programming')], ContestBudgetState(max_turns=5))
        s.select_task('q1')
        s.create_answer('42', author='Agent_1')
        s.select_task('q2')
        selected = _scheduled_agent_task(s, agent='Agent_2', work_task_ids=[], review_task_ids={'q1'}, reported_version_hashes=set())
        self.assertIsNotNone(selected)
        self.assertEqual(selected.task_id, 'q1')

    def test_unavailable_grades_do_not_enter_denominator(self):
        m = ContestManifest('grading', 'custom', (task('known', {'expected_answer':'42'}), task('unknown')))
        result = grade_contest_result(m, {'submissions': {'known':'42', 'unknown':'report'}})
        self.assertFalse(result['graded'])
        self.assertEqual(result['score'], 1)
        self.assertEqual(result['max_score'], 1)
        self.assertEqual(result['task_utility'], 1)
        self.assertEqual(result['evaluation_coverage'], 0.5)
        self.assertIsNone(result['tasks']['unknown']['score'])

    def test_empty_or_wholly_unavailable_grades_are_not_complete(self):
        for tasks in ((), (task('unknown'),)):
            with self.subTest(task_count=len(tasks)):
                result = grade_contest_result(ContestManifest('grading', 'custom', tasks), {})
                self.assertFalse(result['graded'])
                self.assertEqual(result['evaluation_coverage'], 0.0)
                self.assertEqual(result['graded_tasks'], 0)
                self.assertIsNone(result['score'])
                self.assertIsNone(result['task_utility'])

    def test_all_supported_grades_are_complete(self):
        manifest = ContestManifest('grading', 'custom', (task('known', {'expected_answer': '42'}),))
        result = grade_contest_result(manifest, {'submissions': {'known': '42'}})
        self.assertTrue(result['graded'])
        self.assertEqual(result['evaluation_coverage'], 1.0)
        self.assertEqual(result['task_utility'], 1.0)

    def test_reference_only_gold_is_unavailable(self):
        m = ContestManifest('grading', 'custom', (task('report', {'parts':[{'id':'1','expected':'long reference','points':10,'match_mode':'reference_llm'}]}),))
        result = grade_contest_result(m, {'submissions': {'report':'long reference'}})
        self.assertFalse(result['graded'])
        self.assertIsNone(result['task_utility'])

    def test_known_contest_tool_policy_matches_runtime(self):
        names = {s.name for s in _resolved_actions(ContestManifest('arml', 'arml_local', (task('q1'),)))}
        self.assertNotIn('use_calculator', names)
        modeling = {s.name for s in _resolved_actions(ContestManifest('model', 'mcm', (task('q1', competition_type='modeling_report'),)))}
        self.assertIn('execute_code', modeling)
        self.assertNotIn('submit_code', modeling)

    def manifest_fixture(self, root, description, split=True):
        (root/'demo').mkdir()
        row={'problem_id':'p','task_type':'team_contest','problem_description':description,'gold_label':{'parts':[{'id':'1','expected':'SECRET_ONE','points':1},{'id':'2','expected':'SECRET_TWO','points':1}]}}
        (root/'demo/benchmark.json').write_text(json.dumps([row]), encoding='utf-8')
        path=root/'manifest.json'
        path.write_text(json.dumps({'session_id':'audit','competition_id':'demo','problem_ids':['p'],'split_parts':split,'question_ids':['1'] if split else []}), encoding='utf-8')
        return path

    def test_mixed_numbering_split_and_unsplit_prompts_are_answer_blind(self):
        for split in (True, False):
            with self.subTest(split=split), tempfile.TemporaryDirectory() as temp:
                root=Path(temp)
                path=self.manifest_fixture(root, '1. First question\n2) Second question\nTeam Answers 1. SECRET_ONE 2. SECRET_TWO', split)
                m=load_contest_manifest(path, benchmark_root=root)
                self.assertNotIn('SECRET_ONE', m.tasks[0].prompt)
                if split:
                    self.assertEqual([t.task_id for t in m.tasks], ['p:1'])

    def test_explicit_split_failure_raises_instead_of_falling_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            path=self.manifest_fixture(root, 'Unnumbered scanned packet\nTeam Answers 1. SECRET_ONE 2. SECRET_TWO')
            with self.assertRaisesRegex(ValueError, 'split'):
                load_contest_manifest(path, benchmark_root=root)


if __name__ == '__main__':
    unittest.main()
