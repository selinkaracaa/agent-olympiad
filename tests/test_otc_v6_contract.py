"""Executable contract for the user's turn-0-only, reviewed OTC protocol."""
import json
import unittest
from dataclasses import replace
from unittest.mock import Mock

from actions import validate_action_invocation
from action_wire import normalize_invocation
from contest_actions import _apply_action, _task_has_independent_approval
from contest_judging import queue_verdict, deliver_verdicts
from contest_lifecycle import _collect_programming_deadline
from contest_memory import ContestMemory
from contest_session import ContestSession, ContestBudgetState, TaskUnit
from contest_runner import ContestRunConfig, run_contest, _resolved_actions, _actions_for_agent
from rulecard_policy import open_table_policy
from rules.loader import load_rule_card
from strategy import StrategicPolicy
from tool_registry import ACTION_REGISTRY
from test_otc_rulecard import ARML, ICPC, ScriptedLLM, action, arml_manifest, icpc_manifest


class OtcV6ContractTests(unittest.TestCase):
    def table(self):
        config = ContestRunConfig('otc', 3, 60, rule_card=ICPC)
        session = ContestSession([TaskUnit('p1', kind='programming'),
                                  TaskUnit('p2', kind='programming')],
                                 ContestBudgetState(max_turns=60))
        session.consume_budget(turns=3)
        session.select_task('p1')
        session.create_answer('print(42)', author='Agent_1', evidence_refs=('sample',))
        memory = ContestMemory(run_id='r', session_id='s', competition_id='icpc')
        memory.append(task_id='p1', question_id=None, actor='Judge', visibility='public',
                      kind='sample_judge_result', turn=3,
                      payload={'version_hash': session.active_task.versions[-1].version_hash,
                               'sample_verdict': 'AC'})
        return config, session, memory

    def test_all_thirteen_cards_have_the_same_protocol_contract(self):
        names = ('arml_local', 'arml_national_team', 'cfa_research_challenge',
                 'codeforces', 'history_olympiad', 'hmmt_guts', 'icpc',
                 'mystery_hunt', 'nyu_ctf_bench', 'purple_comet', 'qanta',
                 'science_bowl', 'wmtc')
        for name in names:
            with self.subTest(card=name):
                card = load_rule_card(name)
                raw = card.simulation['open_table_coach']
                policy = open_table_policy(card, team_size=card.team_size_default,
                    programming='submit_code' in raw['contestant_turn_policy']['allowed_actions'])
                self.assertEqual(policy.brief_turn, 0)
                self.assertLessEqual(policy.min_turns, card.simulation['max_turns'])
                self.assertTrue(raw['review_required'])

    def test_approval_is_independent_current_and_rejection_is_a_veto(self):
        config, session, memory = self.table()
        specs = _resolved_actions(icpc_manifest(), config)
        names = lambda: {s.name for s in _actions_for_agent(specs, session, config,
                             'Agent_1', memory=memory)}
        self.assertNotIn('submit_code', names())
        with self.assertRaisesRegex(ValueError, 'differ'):
            session.record_review('Agent_1', 'Self approval')
        session.record_review('Agent_2', 'Found a defect', decision='reject')
        self.assertNotIn('submit_code', names())
        session.record_review('Agent_3', 'Looks okay')
        self.assertFalse(_task_has_independent_approval(session.active_task))
        session.create_answer('print(43)', author='Agent_1', evidence_refs=('sample2',))
        self.assertNotIn('submit_code', names())
        session.record_review('Agent_2', 'Checked revised source')
        self.assertIn('submit_code', names())
        self.assertFalse(config.final_review_required)

    def test_shared_keyboard_cannot_be_bypassed_by_switching_problems(self):
        config, session, memory = self.table()
        memory.append(task_id='p1', question_id=None, actor='Agent_1',
                      visibility='private', recipients=('Agent_1',), kind='execute_code',
                      payload={'code': 'print(42)'}, turn=3)
        session.select_task('p2')
        executor = Mock()
        with self.assertRaisesRegex(ValueError, 'workstation'):
            _apply_action(action='execute_code', arguments={'code': 'print(2)'},
                          agent='Agent_2', manifest=icpc_manifest(), session=session,
                          memory=memory, config=config, strategic_policy=StrategicPolicy(),
                          task_action_executor=executor)
        executor.assert_not_called()

    def test_queued_verdict_is_private_and_restored_once(self):
        for verdict in ('AC', 'WA'):
            with self.subTest(verdict=verdict):
                config, session, memory = self.table()
                queue_verdict(session, memory, session.active_task,
                              {'verdict': verdict, 'valid': True, 'secret': 'judge-detail'}, 1, 20)
                deliver_verdicts(session, memory)
                self.assertFalse(session.active_task.locked)
                self.assertEqual(session.active_task.submissions[-1].verdict, 'PENDING')
                self.assertEqual(session.budget.penalty_minutes, 0)
                for agent in ('Agent_1', 'Agent_2', 'Agent_3'):
                    self.assertFalse(any(e.kind in {'verdict_queued', 'reopen', 'submit_code_result'}
                                         for e in memory.view(agent)))
                executor = Mock()
                with self.assertRaisesRegex(ValueError, 'pending|Pending'):
                    _apply_action(action='execute_code', arguments={'code': 'print(9)'},
                        agent='Agent_1', manifest=icpc_manifest(), session=session,
                        memory=memory, config=config, strategic_policy=StrategicPolicy(),
                        task_action_executor=executor)
                executor.assert_not_called()
                session = ContestSession.from_checkpoint(session.checkpoint())
                memory = ContestMemory.from_checkpoint_json(memory.to_checkpoint_json())
                session.consume_budget(turns=1)
                deliver_verdicts(session, memory)
                deliver_verdicts(session, memory)
                self.assertEqual(len(session.task('p1').submissions), 1)
                self.assertEqual(session.task('p1').submissions[0].verdict, verdict)
                self.assertEqual(session.budget.penalty_minutes, 20 if verdict == 'WA' else 0)
                self.assertEqual(len([e for e in memory.view('Agent_2')
                                     if e.kind == 'submit_code_result']), 1)

    def test_final_delivery_and_no_queue_do_not_lose_or_mutate_state(self):
        _, session, memory = self.table()
        before = session.checkpoint()
        deliver_verdicts(session, memory)
        self.assertEqual(before, session.checkpoint())
        queue_verdict(session, memory, session.active_task, {'verdict': 'AC', 'valid': True}, 1, 20)
        deliver_verdicts(session, memory, final=True)
        self.assertTrue(session.task('p1').locked)

    def test_programming_deadline_does_not_waive_approval(self):
        for approved in (False, True):
            _, session, memory = self.table()
            if approved:
                session.record_review('Agent_2', 'Read full source; samples pass')
            executor = Mock(spec=['__call__'], return_value={'verdict': 'AC', 'valid': True})
            _collect_programming_deadline(icpc_manifest(), session, memory, executor,
                                          lambda: None, require_approval=True)
            self.assertEqual(executor.call_count, int(approved))

    def test_math_deadline_only_collects_approved_current_answer(self):
        config = ContestRunConfig('otc', 6, 2, rule_card=ARML)
        scripted = ScriptedLLM({'Agent_1': [action('work', content='Final answer: 42', problem_id='q1')]})
        def query(system, user):
            if 'You are Agent_2' in system and 'private deliberation' not in system.lower():
                rows = json.JSONDecoder().raw_decode(user.split('YOUR ELIGIBLE PENDING REVIEWS\n')[1])[0]
                if rows:
                    row = rows[0]
                    return action('review_answer', problem_id=row['problem_id'],
                                  version_hash=row['version_hash'], decision='approve',
                                  content='Recomputed the answer independently')
            return scripted(system, user)
        result = run_contest(arml_manifest(), query, config)
        self.assertEqual(result['submissions'], {'q1': 'Final answer: 42', 'q2': ''})
        self.assertFalse(result['session_checkpoint']['tasks'][1]['submissions'])

    def test_resume_does_not_call_coach_again(self):
        config = ContestRunConfig('otc', 6, 2, rule_card=ARML)
        llm = ScriptedLLM({})
        checkpoints = []
        def interrupt(session, memory):
            checkpoints.append((session, memory))
            raise RuntimeError('stop after brief')
        with self.assertRaisesRegex(RuntimeError, 'stop after brief'):
            run_contest(arml_manifest(), llm, config, checkpoint_callback=interrupt)
        session, memory = checkpoints[-1]
        result = run_contest(arml_manifest(), llm, config,
                             session_checkpoint=session, memory_checkpoint=memory)
        self.assertEqual(sum(c['kind'] == 'brief' for c in llm.calls), 1)
        self.assertFalse(any(c['kind'] == 'opening' for c in llm.calls))
        self.assertEqual(result['budget']['api_calls_used'], 1 + 2 * 6 * 2)

    def test_aliases_share_normalizer_without_bypassing_dynamic_schema(self):
        rest = ACTION_REGISTRY['rest']
        canonical, arguments, error = validate_action_invocation('sleep', {'reason': 'wait'}, [rest])
        self.assertIsNone(error)
        self.assertEqual(canonical, normalize_invocation('sleep', {'reason': 'wait'}).action)
        frozen = replace(ACTION_REGISTRY['submit_code'], arguments=())
        self.assertIsNotNone(validate_action_invocation('submit_code', {'code': 'print(1)'}, [frozen])[2])
        self.assertIsNotNone(validate_action_invocation('work', {'content': 'x'}, [rest])[2])


if __name__ == '__main__':
    unittest.main()
