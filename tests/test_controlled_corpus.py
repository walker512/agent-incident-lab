"""Captured Codex exec projections; raw-stream authenticity remains operator-attested."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from incidentlab.core import analyze

ROOT = Path(__file__).resolve().parent / 'corpus/controlled'


class ControlledCaptureRegression(unittest.TestCase):
    def test_operator_labels_and_native_exec_correlation(self):
        review = json.loads((ROOT / 'review.json').read_text())
        hashes = {h['name']: h for h in json.loads((ROOT / 'capture_hashes.json').read_text())}
        self.assertEqual(len(review['cases']), 3)
        self.assertEqual(review['sessions_with_command_execution'], 2)
        for case in review['cases']:
            with self.subTest(run=case['id']):
                raw = (ROOT / (case['id'] + '.projected.jsonl')).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), hashes[case['id']]['projected_sha256'])
                # Independent source-field check before exercising the parser.
                rows = [json.loads(line) for line in raw.splitlines()]
                for start, end, status in case['pairs']:
                    call, result = rows[start - 1]['item'], rows[end - 1]['item']
                    self.assertEqual(call['id'], result['id'])
                    self.assertEqual(result['exit_code'], 0 if status == 'success' else 1)
                report = analyze(raw.decode())
                self.assertEqual(report['format'], 'codex-exec')
                self.assertEqual(report['lines'], dict(total=case['records'],
                                 recognized=case['records'], unknown=0, malformed=0))
                self.assertEqual(report['metrics'], dict(toolCalls=case['commands'],
                                 toolResults=case['commands'], failedTools=case['failures'],
                                 pendingTools=0, unknownOutcomes=0))
                self.assertFalse(report['quality']['gate'])
                self.assertEqual(sorted(f['code'] for f in report['findings']),
                                 sorted(case['findings']))
                self.assertEqual([[c['line'], c['resultLine'], c['status']]
                                 for c in report['calls']], case['pairs'])

    def test_projection_has_only_reviewed_structural_fields(self):
        for path in ROOT.glob('*.projected.jsonl'):
            for line in path.read_text().splitlines():
                row = json.loads(line)
                self.assertLessEqual(row.keys(), {'type', 'item'})
                self.assertIn(row['type'], {'thread.started', 'turn.started',
                              'turn.completed', 'item.started', 'item.completed'})
                if 'item' in row:
                    item = row['item']
                    self.assertLessEqual(item.keys(), {'type', 'id', 'status', 'exit_code'})
                    self.assertIn(item['type'], {'command_execution', 'agent_message'})
                    if 'id' in item:
                        self.assertRegex(item['id'], r'^id-[1-4]$')
                    if 'status' in item:
                        self.assertIn(item['status'], {'in_progress', 'failed', 'completed'})
                    if 'exit_code' in item:
                        self.assertIn(item['exit_code'], [0, 1])

    def test_original_failure_programs_in_disposable_directory(self):
        # Executing fixture programs is not executing an agent or replaying its run.
        cases = [('test_example.py', [], 'AssertionError'),
                 ('controlled_cases.py', ['missing'], 'FileNotFoundError'),
                 ('controlled_cases.py', ['invalid-json'], 'JSONDecodeError'),
                 ('controlled_cases.py', ['timeout'], 'TimeoutExpired'),
                 ('controlled_cases.py', ['success'], 'CONTROL_SUCCESS')]
        with tempfile.TemporaryDirectory() as directory:
            for filename, args, marker in cases:
                with self.subTest(args=args):
                    result = subprocess.run([sys.executable, str(ROOT / 'fixtures' / filename), *args],
                                            cwd=directory, text=True, capture_output=True, timeout=10)
                    self.assertEqual(result.returncode, 0 if args == ['success'] else 1)
                    self.assertIn(marker, result.stdout + result.stderr)
