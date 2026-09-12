import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from isolated_python import run_python_isolated, IsolationUnavailable


class IsolatedPythonTests(unittest.TestCase):
    def test_missing_backend_never_falls_back_to_host(self):
        with patch('isolated_python.shutil.which', return_value=None):
            with self.assertRaises(IsolationUnavailable):
                run_python_isolated("raise RuntimeError('must not execute')")

    def test_arithmetic_input_and_host_file_isolation(self):
        with tempfile.TemporaryDirectory() as temp:
            secret=Path(temp)/'private_answer.txt'
            secret.write_text('not mounted', encoding='utf-8')
            source=f"from pathlib import Path\nprint(int(input())*2)\nprint(Path({str(secret)!r}).exists())"
            result=run_python_isolated(source, stdin='21\n')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '42\nFalse\n')

    def test_timeout_and_output_are_bounded(self):
        timeout=run_python_isolated('while True: pass', timeout_sec=0.2)
        self.assertTrue(timeout.timed_out)
        noisy=run_python_isolated("print('x'*100000)", output_bytes=1024)
        self.assertTrue(noisy.output_limited)
        self.assertLessEqual(len(noisy.stdout.encode()),1024)


if __name__ == '__main__':
    unittest.main()
