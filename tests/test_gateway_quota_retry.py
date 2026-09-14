"""Retry only a definitive quota denial, never an uncertain submission."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from judge.vjudge_gateway_client import submit_via_gateway


DENIED = {'status': 'failed', 'verdict': 'SUBMIT_FAILED', 'run_id': '',
          'gateway_run_id': 'denied',
          'message': 'Kattis response did not include a submission ID: You are out of submission tokens. '
                     'Your next token will regenerate in 35 seconds.'}


class GatewayQuotaRetryTests(unittest.TestCase):
    def submit(self, responses):
        with (patch.dict('os.environ', {'VJUDGE_GATEWAY_URL': 'http://localhost:8787'}),
              patch('judge.vjudge_gateway_client.urllib.request.urlopen',
                    side_effect=[io.BytesIO(json.dumps(r).encode()) for r in responses]) as post,
              patch('time.sleep') as sleep):
            result = submit_via_gateway(problem='takeover', language='python3', source='print(1)',
                                        oj='Kattis', idempotency_key='same-attempt')
        return result, post, sleep

    def test_definitive_denial_waits_and_retries_with_stable_child_key(self):
        result, post, sleep = self.submit([DENIED, {'status': 'final', 'verdict': 'WA', 'run_id': '123'}])
        self.assertEqual(result['run_id'], '123')
        payloads = [json.loads(call.args[0].data) for call in post.call_args_list]
        self.assertEqual([p['idempotency_key'] for p in payloads],
                         ['same-attempt', 'same-attempt:quota-retry-1'])
        self.assertEqual(payloads[0]['source'], payloads[1]['source'])
        self.assertEqual(sum(call.args[0] for call in sleep.call_args_list), 36)
        self.assertEqual(result['quota_retries'][0]['gateway_run_id'], 'denied')

    def test_retry_is_bounded(self):
        result, post, _ = self.submit([DENIED, DENIED])
        self.assertEqual(post.call_count, 2)
        self.assertEqual(result['verdict'], 'SUBMIT_FAILED')

    def test_known_run_or_ambiguous_failure_is_never_retried(self):
        for result in [dict(DENIED, run_id='123'),
                       dict(DENIED, remote_run_id='123'),
                       dict(DENIED, vjudge_run_id='123'),
                       dict(DENIED, status='polling'),
                       dict(DENIED, message='Kattis response did not include a submission ID')]:
            with self.subTest(result=result):
                actual, post, sleep = self.submit([result])
                self.assertEqual(actual, result)
                self.assertEqual(post.call_count, 1)
                sleep.assert_not_called()

    def test_network_error_is_not_retried(self):
        with (patch.dict('os.environ', {'VJUDGE_GATEWAY_URL': 'http://localhost:8787'}),
              patch('judge.vjudge_gateway_client.urllib.request.urlopen',
                    side_effect=urllib.error.URLError('timeout')) as post):
            result = submit_via_gateway(problem='takeover', language='python3', source='print(1)', oj='Kattis')
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(post.call_count, 1)
