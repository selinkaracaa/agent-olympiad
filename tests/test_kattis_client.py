from __future__ import annotations

import configparser
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from judge.kattis import KattisClient
from judge.remote import RemoteSubmitRequest


class _Response:
    def __init__(self, *, text: str = "", payload=None, status_code: int = 200):
        self.text = text
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class _Session:
    def __init__(self):
        self.posts = []
        self.gets = []

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        if url.endswith("/login"):
            return _Response(status_code=200)
        return _Response(text="Submission ID: 12345", status_code=200)

    def get(self, url, **kwargs):
        self.gets.append((url, kwargs))
        return _Response(
            payload={
                "status_id": 16,
                "row_html": (
                    '<tr data-submission-id="12345">'
                    '<div class="status">Accepted</div></tr>'
                ),
            }
        )


def _config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(
        {
            "user": {"username": "user", "token": "secret"},
            "kattis": {
                "hostname": "open.kattis.com",
                "loginurl": "https://open.kattis.com/login",
                "submissionurl": "https://open.kattis.com/submit",
                "submissionsurl": "https://open.kattis.com/submissions",
            },
        }
    )
    return cfg


class KattisClientTests(unittest.TestCase):
    def test_submit_and_poll_returns_authoritative_accepted_verdict(self):
        session = _Session()
        client = KattisClient(config=_config(), session=session)

        result = client.submit_and_poll(
            RemoteSubmitRequest(
                oj="Kattis",
                problem="bottles",
                language="python3",
                source="print('candidate')",
            ),
            interval_sec=0,
            timeout_sec=1,
        )

        self.assertEqual(result.status, "final")
        self.assertEqual(result.verdict, "AC")
        self.assertEqual(result.run_id, "12345")
        self.assertEqual(session.posts[1][1]["data"]["language"], "Python 3")
        self.assertEqual(session.posts[1][1]["data"]["mainclass"], "main.py")
        self.assertTrue(session.gets[0][0].endswith("/submissions/12345?json"))


if __name__ == "__main__":
    unittest.main()
