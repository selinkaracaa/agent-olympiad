"""All-track registration preserves blocked jobs and input visibility."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('pipeline', Path(__file__).resolve().parents[1] / 'scripts/run_pipeline.py')
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)


class PipelineTests(unittest.TestCase):
    def test_registration_retains_unrunnable_track_and_never_uses_judge_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pipeline.write(root / 'data/benchmarks/index.json', {'olympiads': [
                {'id': 'proof', 'benchmark_path': 'proof.json'},
                {'id': 'external', 'benchmark_path': 'external.json'}]})
            for name, kind in [('proof', 'proof_packet'), ('external', 'robot')]:
                for component, data in [('competition', {'deliverable': {'official_deliverable': kind}}),
                                        ('collaboration', {}), ('evaluation', {})]:
                    pipeline.write(root / 'data/rules' / name / (component + '.json'), data)
            pipeline.write(root / 'proof.json', [{'problem_id': 'proof_1', 'provenance': {
                'assets': [{'path': 'solutions.pdf', 'role': 'judge_only'}]}}])
            pipeline.write(root / 'external.json', [{'problem_id': 'external_1'}])
            with patch.object(pipeline, 'ROOT', root):
                registry = pipeline.register(root / 'out')
            self.assertEqual(registry['track_count'], 2)
            self.assertEqual(registry['session_count'], 2)
            self.assertTrue(all(j['blockers'] for j in registry['jobs']))
            self.assertNotIn('task_pdf', registry['jobs'][0])

    def test_report_does_not_infer_completion_from_result_file(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            registry = {'jobs': [dict(id='a', competition='arml_local', session='2014',
                                     route='native', blockers=[])]}
            pipeline.write(out / 'runs/a/contest_session.json', {'grade': {'score': 12, 'max_score': 60}})
            pipeline.report(out, registry, {})
            self.assertEqual(pipeline.read(out / 'batch_status.json')['counts'], {'pending': 1})
            self.assertIn('12', (out / 'summary.tsv').read_text())


if __name__ == '__main__':
    unittest.main()
