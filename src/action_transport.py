"""Validate one contest action before handing any call to the executor."""
from __future__ import annotations

import json
from dataclasses import replace

from contest_budget import estimate_tokens
from llm import LLMRequest, LLMResponse, RequestFn


def request_single_action(request_fn: RequestFn, request: LLMRequest) -> LLMResponse:
    """Repair a multi-call response once, charging every generation to budget.

    None of an ambiguous batch executes. The model selects one action against
    the unchanged state; rejected calls remain available for trace auditing.
    Provider/emulation failures with zero calls retain their existing handling.
    """
    # A provider hint reduces invalid generations; the atomic validation below
    # remains authoritative even when a backend ignores this constraint.
    request = replace(request, parallel_tool_calls=False)
    limit = request.metadata.get("max_transport_attempts")
    budget = limit if isinstance(limit, int) else None
    calls_used = tokens_used = retries = 0
    rejected = []
    current = request
    for attempt in range(2):
        response = request_fn(current)
        if len(response.tool_calls) <= 1 and not rejected:
            return response
        calls_used += max(1, int(response.usage.get("api_calls") or 1))
        serialized = json.dumps([{"name": c.name, "arguments": c.arguments}
                                 for c in response.tool_calls], ensure_ascii=False)
        tokens_used += int(response.usage.get("output_tokens")
                           or response.usage.get("completion_tokens")
                           or estimate_tokens(serialized or response.text))
        retries += max(0, int(response.usage.get("tool_retries") or 0))
        if len(response.tool_calls) <= 1:
            break
        rejected.extend({"call_id": c.call_id, "name": c.name,
                         "arguments": c.arguments, "executed": False,
                         "rejection_reason": "multiple_actions_in_one_response"}
                        for c in response.tool_calls)
        if attempt == 1 or (budget is not None and calls_used >= budget):
            response = replace(response, tool_calls=(), usage={
                **response.usage,
                "tool_error": "Response must contain exactly one action; no calls from the batch executed.",
            })
            break
        retries += 1
        current = replace(request, user_prompt=(
            request.user_prompt
            + "\n\nACTION RESPONSE REJECTED\n"
            + "You returned multiple function calls. No action from that response executed. "
            + "The state is unchanged. Select exactly one available function and call it once."
            + "\nYour rejected calls (unexecuted proposals, not tool results):\n"
            + serialized
            + "\nReturn only your selected single call, then wait for its result."
        ), metadata={**request.metadata,
                     "max_transport_attempts": None if budget is None else budget - calls_used})
    return replace(response, usage={
        **response.usage, "api_calls": calls_used, "output_tokens": tokens_used,
        "tool_retries": retries, "rejected_tool_calls": rejected,
    })
