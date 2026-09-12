import unittest

from artifact_contract import ArtifactContract
from artifacts.contest_delivery import validate_source
from contest_adapters import grade_contest_result
from contest_manifest import ContestManifest, ManifestTask
from otc_artifact_pipeline import submission_diagnostics


class PilotRegressionTests(unittest.TestCase):
    def grade(self, gold, answer, competition='qanta'):
        task = ManifestTask('q', 'q', None, 'Question', 'quiz', 1, False,
                            {'gold_label': {'expected_answer': gold}})
        return grade_contest_result(ContestManifest('fixture', competition, (task,)),
                                    {'submissions': {'q': answer}})['score']

    def test_qanta_answerline_markup(self):
        for gold, answer in [('Margaret {Sanger}', 'Margaret Sanger'),
                             ('{Betelgeuse}', 'Betelgeuse'), ('{estuary}', 'estuary')]:
            with self.subTest(gold=gold):
                self.assertEqual(self.grade(gold, answer), 1)

    def test_qanta_does_not_guess_aliases_or_accept_empty(self):
        for answer in ['', 'Gustav Kirchhoff', 'Kirchoff', 'not Gustav Kirchoff']:
            self.assertEqual(self.grade('Gustav Kirchoff', answer), 0)

    def test_markup_cleanup_is_not_applied_to_other_competitions(self):
        self.assertEqual(self.grade('{estuary}', 'estuary', 'math'), 0)

    def test_qanta_single_part_and_question_scoring(self):
        for question_id in (None, '1'):
            task = ManifestTask('q', 'q', question_id, 'Question', 'quiz', 1, False,
                {'gold_label': {'parts': [{'id': '1', 'expected': '{estuary}', 'points': 1}]}})
            grade = grade_contest_result(ContestManifest('fixture', 'qanta', (task,)),
                                         {'submissions': {'q': 'estuary'}})
            self.assertEqual(grade['score'], 1)

    def test_submission_diagnostics_ignore_stale_reviews(self):
        task = {'versions': [{'version_hash': 'v2', 'author': 'A', 'evidence_refs': ['pdf']}],
                'reviews': [{'version_hash': 'v1', 'reviewer': 'B', 'decision': 'reject',
                             'body': 'old', 'stale': True}]}
        self.assertEqual(submission_diagnostics(task, True)['code'], 'awaiting_independent_approval')
        self.assertEqual(submission_diagnostics(task, False)['code'], 'eligible_version_not_submitted')
        task['reviews'].append({'version_hash': 'v2', 'reviewer': 'A', 'decision': 'approve',
                                'body': 'self', 'stale': False})
        self.assertEqual(submission_diagnostics(task, True)['code'], 'awaiting_independent_approval')
        self.assertEqual(submission_diagnostics({'versions': []}, True)['code'], 'no_rendered_version')

    def test_safe_slide_metadata(self):
        validate_source('<html><head><meta charset="utf-8">'
                        '<meta name="viewport" content="width=device-width, initial-scale=1">'
                        '</head><body><h1>Proposal</h1></body></html>', ArtifactContract('slides'))

    def test_active_metadata_stays_blocked(self):
        for meta in ['<meta http-equiv="refresh" content="0;url=https://example.com">',
                     '<meta charset="utf-8" http-equiv="refresh" content="0">',
                     '<meta charset="utf-8" onload="alert(1)">',
                     '<meta charset="utf-8" charset="utf-7">',
                     '<meta name="unknown" content="anything">']:
            with self.subTest(meta=meta), self.assertRaises(ValueError):
                validate_source(meta, ArtifactContract('slides'))


if __name__ == '__main__':
    unittest.main()
