"""Explicit mechanism ablations; these are not OTC or Vanilla presets.

Keep review, cooldown and memory regression coverage independent of the retired
pre-contest Coach protocol. Production callers use ContestRunConfig directly.
"""
from dataclasses import replace

from contest_config import BASELINES, ContestRunConfig


def review_ablation_config(*args, memory=False, **kwargs):
    features = replace(
        BASELINES["decentralized"],
        review_workflow=True,
        memory_actions=memory,
        desk_actions=True,
        private_channel=True,
        structured_context=True,
        submission_cooldown=True,
        mechanical_switch=False,
    )
    return ContestRunConfig("decentralized", *args, features=features, **kwargs)


def run_with_test_plan(manifest, query, config, *, coach_query_fn=None, **kwargs):
    """Use the existing centralized planner to seed mechanism tests.

    The separate scripted plan callback is test data, not a production Coach.
    """
    from contest_runner import run_contest
    if (config.features.coach == "none" and config.features.structured_context
            and coach_query_fn is not None):
        config = replace(config, features=replace(config.features, coach="leader"))
        contestant_query = query
        query = lambda system, user: (
            coach_query_fn(system, user) if user.startswith("OPENING LEADER PLAN")
            else contestant_query(system, user)
        )
    return run_contest(manifest, query, config, coach_query_fn=coach_query_fn, **kwargs)
