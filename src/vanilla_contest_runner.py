"""Vanilla multi-agent contest baseline.

This module is the explicit execution interface for the no-Coach baseline.
It deliberately has no ``coach_query_fn`` parameter, so callers cannot
accidentally enable strategic planning through this seam.
"""

from __future__ import annotations

from typing import Any, Literal

from contest_manifest import ContestManifest
from contest_config import (
    CheckpointCallback,
    ContestRunConfig,
    QueryFn,
    TaskActionExecutor,
)
from contest_engine import _run_contest_engine
from llm import RequestFn


def run_vanilla_contest(
    manifest: ContestManifest,
    query_llm_fn: QueryFn,
    config: ContestRunConfig,
    *,
    action_request_fn: RequestFn | None = None,
    action_transport: Literal["native", "emulated", "prompt_json"] | None = None,
    task_action_executor: TaskActionExecutor | None = None,
    session_checkpoint: dict[str, Any] | None = None,
    memory_checkpoint: str | None = None,
    checkpoint_callback: CheckpointCallback | None = None,
) -> dict[str, Any]:
    """Run the rotating multi-agent baseline without any Coach behavior."""
    if config.features.coach != "none":
        raise ValueError(
            "run_vanilla_contest requires a no-coach baseline "
            "(single_agent or decentralized)"
        )
    return _run_contest_engine(
        manifest,
        query_llm_fn,
        config,
        action_request_fn=action_request_fn,
        action_transport=action_transport,
        coach_query_fn=None,
        task_action_executor=task_action_executor,
        session_checkpoint=session_checkpoint,
        memory_checkpoint=memory_checkpoint,
        checkpoint_callback=checkpoint_callback,
    )
