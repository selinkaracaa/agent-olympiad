from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from judge.remote import RemoteSubmitRequest
from judge.vjudge import (
    VJudgeClient,
    normalize_status,
    problem_num,
    problem_submit_key,
    resolve_language_id,
)
from judge.vjudge_gateway_client import extract_source_and_language


class _FakeResponse:
    def __init__(self, payload, content_type="application/json"):
        if isinstance(payload, (dict, list)):
            raw = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, bytes):
            raw = payload
        else:
            raw = str(payload).encode("utf-8")
        self._raw = raw
        self.headers = {"Content-Type": content_type}

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


CONTEST_HTML = """
<html><body>
<script>
window.C={"endTime":1,"version":"6c3","started":true,"ended":false,
"problems":[{"pid":19984,"title":"Watermelon","oj":"CodeForces","probNum":"4A","num":"A"}]};
</script>
</body></html>
"""


class VJudgeClientTests(unittest.TestCase):
    def test_language_and_problem_helpers(self):
        self.assertEqual(resolve_language_id("cpp17"), "54")
        self.assertEqual(resolve_language_id("python3"), "31")
        self.assertEqual(problem_num("A"), "A")
        self.assertEqual(problem_num("C"), "C")
        self.assertEqual(problem_submit_key(oj="CodeForces", problem="4A"), "CodeForces-4A")
        self.assertEqual(
            problem_submit_key(oj="CodeForces", problem="cf_231A"), "CodeForces-231A"
        )

    def test_normalize_challenge(self):
        verdict, status = normalize_status("Challenge Encountered")
        self.assertEqual(verdict, "CHALLENGE")
        self.assertEqual(status, "needs_human")

    def test_problem_mode_submit_and_poll(self):
        calls = []

        def opener(request, timeout=30):
            calls.append((request.method, request.full_url))
            url = request.full_url
            if url.endswith("/problem/submit/CodeForces-4A"):
                return _FakeResponse({"runId": 72269001})
            if "/solution/data/72269001" in url:
                return _FakeResponse(
                    {"status": "Accepted", "remoteRunId": "388700001", "runtime": 100}
                )
            raise AssertionError(url)

        client = VJudgeClient(cookie="JSESSIONID=abc", method=0, opener=opener)
        result = client.submit_and_poll(
            RemoteSubmitRequest(
                contest_id="",
                oj="CodeForces",
                problem="4A",
                language="python3",
                source="print(1)",
            ),
            interval_sec=0.0,
            timeout_sec=1.0,
        )
        self.assertEqual(result.status, "final")
        self.assertEqual(result.verdict, "AC")
        self.assertEqual(result.run_id, "72269001")
        self.assertTrue(any(url.endswith("/problem/submit/CodeForces-4A") for _, url in calls))

    def test_submit_and_poll_accepted(self):
        calls = []

        def opener(request, timeout=30):
            calls.append((request.method, request.full_url, request.data))
            url = request.full_url
            if url.endswith("/contest/login/845103"):
                return _FakeResponse({})
            if url.endswith("/contest/845103") and request.method == "GET":
                return _FakeResponse(CONTEST_HTML, content_type="text/html")
            if url.endswith("/contest/845103/submitMethods"):
                return _FakeResponse(
                    {
                        "myBindings": [
                            {"oj": "CodeForces", "bindingId": 319071, "accountId": "x"}
                        ]
                    }
                )
            if url.endswith("/contest/submit/845103/A"):
                return _FakeResponse({"runId": 72267448})
            if "/solution/data/72267448" in url:
                return _FakeResponse(
                    {"status": "Accepted", "remoteRunId": "388603095", "runtime": 226}
                )
            raise AssertionError(url)

        client = VJudgeClient(
            cookie="JSESSIONID=abc",
            access_code="123456",
            method=1,
            opener=opener,
        )
        result = client.submit_and_poll(
            RemoteSubmitRequest(
                contest_id="845103",
                problem="A",
                language="cpp17",
                source="#include <bits/stdc++.h>\nint main(){return 0;}",
            ),
            interval_sec=0.0,
            timeout_sec=1.0,
        )
        self.assertEqual(result.status, "final")
        self.assertEqual(result.verdict, "AC")
        self.assertEqual(result.run_id, "72267448")
        self.assertEqual(result.remote_run_id, "388603095")
        self.assertGreaterEqual(len(calls), 4)

    def test_cloudflare_interstitial_needs_human(self):
        def opener(request, timeout=30):
            return _FakeResponse(
                "Enable JavaScript and cookies to continue",
                content_type="text/html",
            )

        client = VJudgeClient(cookie="JSESSIONID=abc", access_code="1", opener=opener)
        result = client.submit(
            RemoteSubmitRequest(
                contest_id="845103",
                problem="A",
                language="python3",
                source="print(1)",
            )
        )
        self.assertEqual(result.status, "needs_human")
        self.assertEqual(result.verdict, "CHALLENGE")

    def test_extract_cpp_source(self):
        source, language = extract_source_and_language(
            "```cpp\n#include <iostream>\nint main(){}\n```"
        )
        self.assertEqual(language, "cpp17")
        self.assertIn("#include", source)


if __name__ == "__main__":
    unittest.main()
