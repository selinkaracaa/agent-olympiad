import copy
import unittest

from scripts.restore_review_catalog import ROOT, numeric, read, restore


class RestoreReviewTests(unittest.TestCase):
    def test_restore_preserves_current_and_is_idempotent(self):
        rows = [{'problem_id': 'existing', 'curation': 'keep'}]
        archived = [dict(dataset='test', reason='missing packet', row={'problem_id': 'new'}),
                    dict(dataset='test', reason='old', row={'problem_id': 'existing'}),
                    dict(dataset='envirothon', reason='excluded', row={'problem_id': 'excluded'})]
        before = copy.deepcopy(rows)
        result = restore(rows, archived)
        self.assertEqual(rows, before)
        self.assertEqual(result[0], rows[0])
        self.assertEqual([r['problem_id'] for r in result], ['existing', 'new'])
        self.assertEqual(result, restore(result, archived))
        self.assertEqual(result[1]['evaluation']['status'], 'not_ready')

    def test_catalog_and_scorecards(self):
        index = read('data/benchmarks/index.json')
        self.assertNotIn('envirothon', [t['id'] for t in index['olympiads']])
        total = 0
        for track in index['olympiads']:
            rows = read(track['benchmark_path'])
            total += len(rows)
            self.assertEqual(len(rows), track['problems_collected'])
            self.assertEqual(len(rows), len({r['problem_id'] for r in rows}))
            for r in rows:
                e = r.get('evaluation', {})
                if e.get('rubric_reuse'):
                    self.assertEqual(e['rubric_reuse']['source_competition'], track['id'])
                    self.assertEqual(e['rubric_reuse']['target_competition'], track['id'])
                    self.assertFalse(e['rubric_reuse']['official_year_equivalence'])
                    cards = read(e['scorecard_path'])['records']
                    card = next(c for c in cards if c['problem_id'] == r['problem_id'])
                    self.assertEqual(card['evaluation_status'], e['status'])
                    if e['status'] == 'ready_with_limitations':
                        self.assertTrue(numeric(e['rubric_path']))
                if r.get('restoration_review'):
                    self.assertEqual(e['status'], 'not_ready')
        self.assertEqual(total, index['total_records'])

    def test_report_subtotal_is_not_official_tournament_score(self):
        rubric = read('data/rubrics/ichto_report_scientific_9_reused_v1.json')
        self.assertEqual(rubric['source_edition'], 2025)
        self.assertEqual(rubric['total_points'], 9)
        self.assertEqual(sum(c['max_score'] for c in rubric['criteria']), 9)
        self.assertTrue((ROOT / rubric['source_rubric_path']).exists())


if __name__ == '__main__':
    unittest.main()
