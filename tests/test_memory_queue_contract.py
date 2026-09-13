"""Queued memory ablation and explicit query/decision contract."""
import unittest
from dataclasses import asdict

from action_modules.memory import agent_context
from contest_config import BASELINES, ContestRunConfig
from contest_memory import ContestMemory
from contest_policy import _resolved_actions
from rules.loader import load_rule_card, DEFAULT_RULES_ROOT
from rules.storage import iter_rule_card_ids
from test_otc_rulecard import arml_manifest


class MemoryQueueContractTests(unittest.TestCase):
    def test_otc_pair_differs_only_in_memory_and_keeps_all_card_policies(self):
        plain, memory = (asdict(BASELINES[name]) for name in ('vallina_otc', 'otc'))
        self.assertEqual({k for k in plain if plain[k] != memory[k]}, {'memory_actions'})
        for competition in iter_rule_card_ids(DEFAULT_RULES_ROOT):
            with self.subTest(competition=competition):
                card = load_rule_card(competition)
                configs = [ContestRunConfig(name, card.team_size_default, 3, rule_card=card)
                           for name in ('vallina_otc', 'otc')]
                self.assertEqual(configs[0].otc_policy, configs[1].otc_policy)
                self.assertTrue(all(c.review_required for c in configs))
        card = load_rule_card('arml_local')
        names = [{s.name for s in _resolved_actions(arml_manifest(),
                  ContestRunConfig(name, card.team_size_default, 3, rule_card=card))}
                 for name in ('vallina_otc', 'otc')]
        self.assertEqual(names[1] - names[0], {'remember', 'recall', 'share_note'})
        self.assertFalse(names[0] - names[1])

    def store(self):
        return ContestMemory(run_id='r', session_id='s', competition_id='arml_local')

    def note(self, memory, content, *, actor='Agent_1', visibility='private', turn=1):
        return memory.append(task_id='p1', question_id=None, actor=actor,
            visibility=visibility, kind='note' if visibility == 'private' else 'note_shared',
            payload={'content': content}, turn=turn)

    def test_nonempty_query_does_not_return_unrelated_notes(self):
        memory = self.store()
        self.note(memory, 'Use a generating function for the recurrence.')
        self.note(memory, 'Check the geometry diagram.')
        self.assertEqual(memory.recall('Agent_1', query='network flow', problem_id='p1'), [])
        result = memory.recall('Agent_1', query='generating function')
        self.assertEqual(len(result), 1)
        self.assertIn('generating function', result[0]['content'])
        self.assertEqual(len(memory.recall('Agent_1')), 2)  # Explicit browse remains supported.
        self.note(memory, 'The variable x is bounded.')
        self.assertEqual(len(memory.recall('Agent_1', query='x')), 1)

    def test_recall_status_respects_visibility_and_memory_switch(self):
        memory = self.store()
        self.note(memory, 'Hidden token CANARY', actor='Agent_2')
        context = agent_context(memory, viewer='Agent_1', enabled=True, current_task_id='p1')
        self.assertEqual(context['recall_status']['status'], 'empty')
        self.assertEqual(context['recall_status']['visible_note_count'], 0)
        self.note(memory, 'Public recurrence result', actor='Agent_2', visibility='public')
        context = agent_context(memory, viewer='Agent_1', enabled=True, current_task_id='p1')
        self.assertEqual(context['recall_status']['visible_note_count'], 1)
        self.assertNotIn('CANARY', str(context))
        disabled = agent_context(memory, viewer='Agent_1', enabled=False, current_task_id='p1')
        self.assertNotIn('recall_status', str(disabled))
        self.assertNotIn('Public recurrence result', str(disabled))

    def test_recent_query_reports_whether_visible_notes_changed(self):
        from action_modules.memory import recall_notes
        memory = self.store()
        self.note(memory, 'DP complexity bound')
        recall_notes(memory, agent='Agent_1', query='DP', problem_id='p1', event_task_id='p1', turn=2)
        context = agent_context(memory, viewer='Agent_1', enabled=True, current_task_id='p1')
        self.assertFalse(context['recall_status']['notes_changed_since_last_recall'])
        self.note(memory, 'Private other-agent note', actor='Agent_2', turn=3)
        context = agent_context(memory, viewer='Agent_1', enabled=True, current_task_id='p1')
        self.assertFalse(context['recall_status']['notes_changed_since_last_recall'])
        self.note(memory, 'New counterexample', turn=4)
        context = agent_context(memory, viewer='Agent_1', enabled=True, current_task_id='p1')
        self.assertTrue(context['recall_status']['notes_changed_since_last_recall'])
        restored = ContestMemory.from_checkpoint_json(memory.to_checkpoint_json())
        self.assertEqual(restored.recall_status('Agent_1', current_task_id='p1'),
                         memory.recall_status('Agent_1', current_task_id='p1'))

    def test_recall_guidance_reaches_think_and_action_without_forcing_retrieval(self):
        from contest_runner import run_contest
        from test_otc_rulecard import ScriptedLLM, action
        card = load_rule_card('arml_local')
        for variant in ('otc_rule_card', 'otc_rule_card_memory'):
            with self.subTest(variant=variant):
                config = ContestRunConfig(variant, card.team_size_default, 3, rule_card=card)
                llm = ScriptedLLM({f'Agent_{i}': [action('rest', reason='no missing prior fact')] * 3
                                   for i in range(1, card.team_size_default + 1)})
                result = run_contest(arml_manifest(), llm, config, coach_query_fn=llm)
                decision_calls = [c for c in llm.calls if 'one contestant' in c['system']]
                self.assertTrue(any('PRIVATE deliberation' in c['system'] for c in decision_calls))
                self.assertTrue(any('Return exactly one JSON' in c['system'] for c in decision_calls))
                for call in decision_calls:
                    if config.modules.memory:
                        self.assertIn('MEMORY DECISION:', call['system'])
                        self.assertIn('recall_status', call['user'])
                        self.assertIn('notes_changed_since_last_recall', call['user'])
                    else:
                        self.assertNotIn('MEMORY DECISION:', call['system'])
                        self.assertNotIn('recall_status', call['user'])
                self.assertFalse(any(e['kind'] == 'recall_result' for e in result['memory']['events']))
                self.assertEqual(result['budget']['api_calls_used'], len(llm.calls))
