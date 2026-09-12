from __future__ import annotations

import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from llm import (  # noqa: E402
    LLMRequest,
    LLMToolCall,
    make_perplexity_responses_caller,
    parse_response_tool_calls,
)


class FunctionCallingTransportTests(unittest.TestCase):
    def test_parses_openai_style_function_call_output(self) -> None:
        calls = parse_response_tool_calls(
            {
                "output": [
                    {
                        "type": "function_call",
                        "call_id": "call-1",
                        "name": "speak",
                        "arguments": '{"content":"hello"}',
                    }
                ]
            }
        )

        self.assertEqual(
            calls,
            (
                LLMToolCall(
                    name="speak",
                    arguments={"content": "hello"},
                    call_id="call-1",
                ),
            ),
        )

    def test_rejects_malformed_function_arguments(self) -> None:
        with self.assertRaisesRegex(ValueError, "arguments"):
            parse_response_tool_calls(
                {
                    "output": [
                        {
                            "type": "function_call",
                            "name": "speak",
                            "arguments": "not-json",
                        }
                    ]
                }
            )

    def test_request_carries_native_tool_contract(self) -> None:
        request = LLMRequest(
            system_prompt="system",
            user_prompt="user",
            tools=(
                {
                    "type": "function",
                    "name": "speak",
                    "parameters": {"type": "object"},
                },
            ),
            tool_choice="required",
        )
        self.assertEqual(request.tools[0]["name"], "speak")
        self.assertEqual(request.tool_choice, "required")

    def test_perplexity_sends_tools_and_returns_function_calls(self) -> None:
        http_response = Mock()
        http_response.ok = True
        http_response.json.return_value = {
            "output": [
                {
                    "type": "function_call",
                    "call_id": "call-1",
                    "name": "speak",
                    "arguments": '{"content":"hello"}',
                }
            ],
            "usage": {"output_tokens": 7},
        }
        with (
            patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}),
            patch("requests.post", return_value=http_response) as post,
        ):
            caller = make_perplexity_responses_caller(
                "test-model",
                max_output_tokens=99,
                temperature=0.0,
            )
            result = caller(
                LLMRequest(
                    system_prompt="system",
                    user_prompt="user",
                    tools=(
                        {
                            "type": "function",
                            "name": "speak",
                            "description": "Broadcast.",
                            "parameters": {"type": "object"},
                        },
                    ),
                    tool_choice="required",
                )
            )

        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["tools"][0]["name"], "speak")
        self.assertEqual(payload["tool_choice"], "required")
        self.assertEqual(payload["max_output_tokens"], 99)
        self.assertEqual(result.tool_calls[0].arguments, {"content": "hello"})
        self.assertEqual(result.text, "")


if __name__ == "__main__":
    unittest.main()
