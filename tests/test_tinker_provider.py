from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import llm
import run_competition_batch as batch


MODEL = "Qwen/Qwen3.6-35B-A3B"


class TransientTinkerError(Exception):
    pass


def _native_sdk(encoded, decoded="  exact response\n", sequences=None):
    tokenizer = Mock()
    tokenizer.apply_chat_template.return_value = encoded
    tokenizer.decode.return_value = decoded
    client = Mock()
    client.get_tokenizer.return_value = tokenizer
    response = SimpleNamespace(
        sequences=(
            [SimpleNamespace(tokens=[7, 8], stop_reason="stop")]
            if sequences is None
            else sequences
        )
    )
    result = Mock()
    result.result.return_value = response
    client.sample.return_value = result
    service = Mock()
    service.create_sampling_client.return_value = client
    sdk = SimpleNamespace(
        ServiceClient=Mock(return_value=service),
        ModelInput=SimpleNamespace(from_ints=Mock(return_value="model-input")),
        SamplingParams=Mock(return_value="sampling-params"),
        APIConnectionError=TransientTinkerError,
    )
    return sdk, service, client, tokenizer, result


class TinkerCallerTests(unittest.TestCase):
    def test_requires_only_api_key_and_initializes_lazily(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "TINKER_API_KEY"):
                llm.make_tinker_caller(MODEL)
        sdk, *_ = _native_sdk([1, 2])
        with patch.dict(os.environ, {"TINKER_API_KEY": "secret"}, clear=True), patch.dict(
            sys.modules, {"tinker": sdk}
        ):
            llm.make_tinker_caller(MODEL)
        sdk.ServiceClient.assert_not_called()

    def test_normalizes_tinker_prefixed_api_key(self):
        sdk, *_ = _native_sdk([1, 2])
        with patch.dict(
            os.environ,
            {"TINKER_API_KEY": "tinker:tml-abc123 这个是注释"},
            clear=True,
        ), patch.dict(sys.modules, {"tinker": sdk}):
            llm.make_tinker_caller(MODEL)
            self.assertEqual(os.environ["TINKER_API_KEY"], "tml-abc123")

    def test_native_request_supports_batch_encoding_and_list_outputs(self):
        for encoded in ({"input_ids": [1, 2, 3]}, [1, 2, 3]):
            with self.subTest(encoded_type=type(encoded).__name__):
                sdk, service, client, tokenizer, result = _native_sdk(encoded)
                with patch.dict(
                    os.environ, {"TINKER_API_KEY": "secret"}, clear=True
                ), patch.dict(sys.modules, {"tinker": sdk}):
                    caller = llm.make_tinker_caller(
                        MODEL, max_output_tokens=321, temperature=0.4
                    )
                    self.assertEqual(
                        caller("system card", "problem"), "exact response"
                    )
                    self.assertEqual(
                        caller("system card", "problem"), "exact response"
                    )

                sdk.ServiceClient.assert_called_once_with()
                service.create_sampling_client.assert_called_once_with(base_model=MODEL)
                client.get_tokenizer.assert_called_once_with()
                tokenizer.apply_chat_template.assert_called_with(
                    [
                        {"role": "system", "content": "system card"},
                        {"role": "user", "content": "problem"},
                    ],
                    tokenize=True,
                    add_generation_prompt=True,
                    enable_thinking=False,
                )
                self.assertEqual(sdk.ModelInput.from_ints.call_count, 2)
                sdk.ModelInput.from_ints.assert_called_with([1, 2, 3])
                sdk.SamplingParams.assert_called_with(
                    max_tokens=321, temperature=0.4
                )
                client.sample.assert_called_with(
                    "model-input",
                    num_samples=1,
                    sampling_params="sampling-params",
                )
                result.result.assert_called()
                tokenizer.decode.assert_called_with(
                    [7, 8], skip_special_tokens=True
                )

    def test_retries_only_transient_sampling_failures_and_sanitizes(self):
        sdk, _, client, tokenizer, result = _native_sdk([1])
        result.result.side_effect = [
            TransientTinkerError("temporary"),
            SimpleNamespace(
                sequences=[SimpleNamespace(tokens=[9], stop_reason="stop")]
            ),
        ]
        tokenizer.decode.return_value = "ok"
        with patch.dict(
            os.environ, {"TINKER_API_KEY": "top-secret"}, clear=True
        ), patch.dict(sys.modules, {"tinker": sdk}), patch.object(
            llm.time, "sleep"
        ) as sleep:
            caller = llm.make_tinker_caller(MODEL)
            self.assertEqual(caller("s", "u"), "ok")
            sleep.assert_called_once_with(1)

            result.result.side_effect = TransientTinkerError(
                "failed with top-secret"
            )
            with self.assertRaisesRegex(RuntimeError, r"\[REDACTED\]") as caught:
                caller("s", "u")
        self.assertNotIn("top-secret", str(caught.exception))
        self.assertEqual(result.result.call_count, 5)

    def test_auth_failure_is_not_retried_and_is_sanitized(self):
        sdk, *_ = _native_sdk([1])
        sdk.ServiceClient.side_effect = RuntimeError("auth top-secret")
        with patch.dict(
            os.environ, {"TINKER_API_KEY": "top-secret"}, clear=True
        ), patch.dict(sys.modules, {"tinker": sdk}), patch.object(
            llm.time, "sleep"
        ) as sleep:
            caller = llm.make_tinker_caller(MODEL)
            with self.assertRaisesRegex(RuntimeError, "initialization failed") as caught:
                caller("s", "u")
        self.assertNotIn("top-secret", str(caught.exception))
        sdk.ServiceClient.assert_called_once_with()
        sleep.assert_not_called()

    def test_rejects_no_sequences_and_empty_decode(self):
        cases = [
            ([], "ignored", "no sampled sequences"),
            ([SimpleNamespace(tokens=[1], stop_reason="length")], " ", "empty decoded"),
        ]
        for sequences, decoded, error in cases:
            with self.subTest(error=error):
                sdk, *_ = _native_sdk([1], decoded=decoded, sequences=sequences)
                with patch.dict(
                    os.environ, {"TINKER_API_KEY": "secret"}, clear=True
                ), patch.dict(sys.modules, {"tinker": sdk}):
                    caller = llm.make_tinker_caller(MODEL)
                    with self.assertRaisesRegex(RuntimeError, error):
                        caller("s", "u")


class TinkerRequestFnTests(unittest.TestCase):
    def test_make_tinker_request_fn_adapts_to_request_interface(self):
        sdk, *_ = _native_sdk([1, 2])
        with patch.dict(os.environ, {"TINKER_API_KEY": "secret"}, clear=True), patch.dict(
            sys.modules, {"tinker": sdk}
        ):
            request_fn = llm.make_tinker_request_fn(MODEL)
            response = request_fn(
                llm.LLMRequest(system_prompt="sys", user_prompt="user")
            )
        self.assertEqual(response.text, "exact response")
        self.assertEqual(response.provider, "tinker")
        self.assertEqual(response.model, MODEL)

    def test_resolve_request_fn_supports_tinker(self):
        sdk, *_ = _native_sdk([1, 2])
        with patch.dict(os.environ, {"TINKER_API_KEY": "secret"}, clear=True), patch.dict(
            sys.modules, {"tinker": sdk}
        ):
            request_fn = llm.resolve_request_fn(provider="tinker", model=MODEL)
            response = request_fn(
                llm.LLMRequest(system_prompt="sys", user_prompt="user")
            )
        self.assertEqual(response.provider, "tinker")
        self.assertEqual(response.text, "exact response")


class CompetitionProviderTests(unittest.TestCase):
    def test_tinker_model_default_and_environment_override(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(batch._resolve_model("tinker", None), MODEL)
        with patch.dict(os.environ, {"TINKER_MODEL": "custom/model"}, clear=True):
            self.assertEqual(
                batch._resolve_model("tinker", None),
                "custom/model",
            )
        self.assertEqual(
            batch._resolve_model("tinker", "explicit/model"),
            "explicit/model",
        )

    def test_provider_selection(self):
        tinker = Mock(return_value="tinker-call")
        perplexity = Mock(return_value="pplx-call")
        with patch.object(batch, "make_tinker_caller", tinker), patch.object(
            batch, "make_perplexity_caller", perplexity
        ):
            self.assertEqual(
                batch._make_live_query("tinker", MODEL), "tinker-call"
            )
            self.assertEqual(
                batch._make_live_query("perplexity", "pplx-model"), "pplx-call"
            )
        tinker.assert_called_once_with(
            model=MODEL,
            max_output_tokens=batch.TINKER_DEFAULT_MAX_TOKENS,
            temperature=batch.TINKER_DEFAULT_TEMPERATURE,
        )
        perplexity.assert_called_once_with(model="pplx-model")

    def test_exact_problem_requires_one_competition(self):
        self.assertEqual(
            batch._select_cases("icpc", "different_problem", None),
            [("icpc", "different_problem")],
        )
        for competitions in (None, "icpc,iiot"):
            with self.subTest(competitions=competitions):
                with self.assertRaisesRegex(ValueError, "exactly one"):
                    batch._select_cases(competitions, "problem", None)

    def test_tinker_without_judges_needs_no_perplexity_key(self):
        captured = []

        def fake_run_one(competition, problem_id, **kwargs):
            captured.append((competition, problem_id, kwargs))
            return {
                "status": "ok",
                "turns_used": 2,
                "max_turns": 2,
                "api_calls": 6,
                "grade_method": "sample_io",
                "grade_score": 1,
                "grade_max_score": 1,
                "coordination_score": None,
                "submitted": True,
                "graded": True,
                "rules_coverage": "covered",
            }

        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"TINKER_API_KEY": "secret"},
            clear=True,
        ), patch.object(batch, "_make_live_query", return_value=Mock()), patch.object(
            batch, "run_one", side_effect=fake_run_one
        ), patch.object(
            sys,
            "argv",
            [
                "run_competition_batch.py",
                "--live",
                "--provider",
                "tinker",
                "--model",
                MODEL,
                "--competitions",
                "icpc",
                "--problem-id",
                "icpc_wf_2012_bottles",
                "--no-judge-task",
                "--no-judge-collab",
                "--output",
                directory,
            ],
        ):
            batch.main()

            summary = json.loads(
                (Path(directory) / "competition_batch.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(summary["provider"], "tinker")
        self.assertEqual(summary["model"], MODEL)
        self.assertEqual(summary["max_output_tokens"], 8192)
        self.assertEqual(summary["temperature"], 0.2)
        self.assertFalse(summary["judge_task"])
        self.assertFalse(summary["judge_collab"])
        self.assertEqual(captured[0][:2], ("icpc", "icpc_wf_2012_bottles"))

    def test_tinker_judge_collab_uses_tinker_without_perplexity_key(self):
        captured = {}

        def fake_resolve_request_fn(**kwargs):
            captured.update(kwargs)
            return Mock(return_value=llm.LLMResponse(text="{}", provider="tinker", model=MODEL))

        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"TINKER_API_KEY": "secret"},
            clear=True,
        ), patch.object(batch, "_make_live_query", return_value=Mock()), patch.object(
            batch, "run_one",
            return_value={
                "status": "ok",
                "turns_used": 2,
                "max_turns": 2,
                "api_calls": 6,
                "grade_method": "sample_io",
                "grade_score": 1,
                "grade_max_score": 1,
                "coordination_score": 0.8,
                "submitted": True,
                "graded": True,
                "rules_coverage": "covered",
            },
        ), patch.object(
            batch, "resolve_request_fn", side_effect=fake_resolve_request_fn
        ), patch.object(
            sys,
            "argv",
            [
                "run_competition_batch.py",
                "--live",
                "--provider",
                "tinker",
                "--model",
                MODEL,
                "--competitions",
                "icpc",
                "--problem-id",
                "icpc_wf_2012_bottles",
                "--no-judge-task",
                "--max-turns",
                "2",
                "--output",
                directory,
            ],
        ):
            batch.main()

            summary = json.loads(
                (Path(directory) / "competition_batch.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(captured["provider"], "tinker")
        self.assertEqual(captured["model"], MODEL)
        self.assertTrue(summary["judge_collab"])
        self.assertEqual(summary["judge_provider"], "tinker")

    def test_midrun_failure_still_writes_complete_sanitized_transcript(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"TINKER_API_KEY": "never-print-this"}, clear=True
        ):
            row = batch.run_one(
                "icpc",
                "icpc_wf_2012_bottles",
                schema="centralized",
                query_fn=lambda _system, _user: (_ for _ in ()).throw(
                    RuntimeError("request failed: never-print-this")
                ),
                request_fn=None,
                rounds=2,
                synthesize=False,
                judge_task=False,
                judge_collab=False,
                out_dir=Path(directory),
                rules_mode="enforced",
                provider="tinker",
                model=MODEL,
                max_output_tokens=8192,
                temperature=0.2,
            )
            transcript = json.loads(
                Path(row["transcript_path"]).read_text(encoding="utf-8")
            )

        serialized = json.dumps(transcript)
        self.assertEqual(row["status"], "error")
        self.assertNotIn("never-print-this", serialized)
        self.assertEqual(transcript["run"]["provider"], "tinker")
        self.assertEqual(transcript["run"]["model"], MODEL)
        self.assertEqual(transcript["run"]["max_output_tokens"], 8192)
        self.assertEqual(transcript["run"]["temperature"], 0.2)
        self.assertEqual(transcript["run"]["schema"], "centralized")
        self.assertEqual(transcript["run"]["rules_mode"], "enforced")
        self.assertIn("final_result", transcript["run"])


if __name__ == "__main__":
    unittest.main()
