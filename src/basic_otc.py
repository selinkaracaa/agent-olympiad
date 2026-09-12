"""Pure basic-OTC overlay. Original rule cards and full OTC are never mutated."""
from copy import deepcopy
from dataclasses import replace
from rulecard_policy import DiscussionPolicy


def basic_policy(policy):
    return replace(policy, discussion=DiscussionPolicy(), deliberation_mode='none',
                   min_challenges=0,
                   memory_entries=replace(policy.memory_entries, private_think_per_agent=1))


def basic_prompt_card(card):
    simulation = deepcopy(card.simulation)
    block = simulation['open_table_coach']
    block.update(review_required=False, protocol_version='vallina_otc_v1',
                 action_bundles=['common', 'desk', 'competition_tools'],
                 status='basic_otc_ablation_not_official_competition_rule')
    turn = block['contestant_turn_policy']
    turn.update(final_submission='current_answer_sheet', discussion_policy={},
                memory_entries={'current_turn_think_only': True})
    delivery = simulation.get('deliverable_pipeline')
    if delivery:
        delivery['review_rendered_version'] = False
    return replace(card, simulation=simulation,
                   deliberation={'mode': 'none', 'reason': 'basic OTC ablation'})
