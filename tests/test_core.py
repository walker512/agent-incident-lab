"""Synthetic structural cases, not evidence of producer-version compatibility."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from incidentlab.core import InputError, analyze, bundle, project, verify_bundle


def jsonl(*rows):
    return '\n'.join(json.dumps(row) for row in rows) + '\n'


def claude_pair(failed=False):
    return [
        {'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'id': 'synthetic-call', 'name': 'Bash', 'input': {}}]}},
        {'type': 'user', 'message': {'content': [
            {'type': 'tool_result', 'tool_use_id': 'synthetic-call',
             'content': 'synthetic output', 'is_error': failed}]}},
    ]


def codes(report):
    return {finding['code'] for finding in report['findings']}


class ParserRegression(unittest.TestCase):
    def test_claude_pair_success_and_explicit_failure(self):
        for failed in (False, True):
            with self.subTest(failed=failed):
                report = analyze(jsonl(*claude_pair(failed)))
                self.assertEqual(report['format'], 'claude')
                self.assertEqual(report['metrics']['toolCalls'], 1)
                self.assertEqual(report['metrics']['toolResults'], 1)
                self.assertEqual(report['metrics']['failedTools'], int(failed))
                self.assertEqual(report['quality']['gate'], not failed)

    def test_malformed_claude_call_record_is_atomic(self):
        for bad_first in (False, True):
            rows = claude_pair()
            blocks = rows[0]['message']['content']
            blocks.insert(0 if bad_first else len(blocks), 'not-a-block')
            report = analyze(jsonl(*rows))
            self.assertEqual(report['lines']['malformed'], 1)
            self.assertEqual(report['metrics']['toolCalls'], 0)
            self.assertIn('orphan_result', codes(report))

    def test_malformed_duplicate_does_not_poison_valid_call(self):
        call, result = claude_pair()
        malformed = copy.deepcopy(call)
        malformed['message']['content'].append({'type': 'tool_use', 'id': None,
                                               'name': 'Bash', 'input': {}})
        report = analyze(jsonl(call, malformed, result))
        self.assertEqual(report['metrics']['toolCalls'], 1)
        self.assertEqual(report['calls'][0]['status'], 'success')
        self.assertNotIn('duplicate_call_id', codes(report))
        self.assertEqual(report['lines']['malformed'], 1)

    def test_malformed_claude_result_record_is_atomic(self):
        for bad_first in (False, True):
            call, result = claude_pair()
            bad_result = copy.deepcopy(result)
            blocks = bad_result['message']['content']
            blocks.insert(0 if bad_first else len(blocks), {'type': 'tool_result',
                          'tool_use_id': None, 'content': 'synthetic'})
            pending = analyze(jsonl(call, bad_result))
            self.assertEqual(pending['metrics']['toolResults'], 0)
            self.assertIn('missing_result', codes(pending))
            completed = analyze(jsonl(call, bad_result, result))
            self.assertEqual(completed['calls'][0]['status'], 'success')
            self.assertNotIn('duplicate_result', codes(completed))

    def test_codex_exec_lifecycle(self):
        for exit_code in (0, 7):
            with self.subTest(exit_code=exit_code):
                report = analyze(jsonl(
                    {'type': 'item.started', 'item': {'type': 'command_execution',
                     'id': 'synthetic-item', 'status': 'in_progress'}},
                    {'type': 'item.completed', 'item': {'type': 'command_execution',
                     'id': 'synthetic-item', 'status': 'completed', 'exit_code': exit_code}}))
                self.assertEqual(report['format'], 'codex-exec')
                self.assertEqual(report['metrics']['toolCalls'], 1)
                self.assertEqual(report['metrics']['toolResults'], 1)
                self.assertEqual(report['quality']['gate'], exit_code == 0)

    def test_codex_session_opaque_result_is_not_success(self):
        report = analyze(jsonl(
            {'type': 'response_item', 'payload': {'type': 'function_call',
             'call_id': 'synthetic-call', 'name': 'exec_command', 'arguments': '{}'}},
            {'type': 'response_item', 'payload': {'type': 'function_call_output',
             'call_id': 'synthetic-call', 'output': 'looks successful but is opaque'}}))
        self.assertEqual(report['format'], 'codex-session')
        self.assertEqual(report['metrics']['unknownOutcomes'], 1)
        self.assertIn('unknown_outcome', codes(report))
        self.assertFalse(report['quality']['gate'])

    def test_missing_result_and_orphan_are_not_success(self):
        call, result = claude_pair()
        for row, expected in ((call, 'missing_result'), (result, 'orphan_result')):
            with self.subTest(expected=expected):
                report = analyze(jsonl(row))
                self.assertIn(expected, codes(report))
                self.assertFalse(report['quality']['gate'])

    def test_duplicate_id_makes_correlation_ambiguous(self):
        call, result = claude_pair()
        report = analyze(jsonl(call, call, result))
        self.assertIn('duplicate_call_id', codes(report))
        self.assertEqual(report['metrics']['unknownOutcomes'], 1)
        self.assertFalse(report['quality']['gate'])

    def test_unknown_content_is_visible(self):
        rows = claude_pair()
        rows[0]['message']['content'].append({'type': 'future_synthetic_block'})
        report = analyze(jsonl(*rows))
        self.assertEqual(report['lines']['unknown'], 1)
        self.assertIn('unrecognized_records', codes(report))
        self.assertFalse(report['quality']['gate'])

    def test_mixed_and_unsupported_formats_have_null_metrics(self):
        inputs = [jsonl({'invented': 'format'}),
                  jsonl(*claude_pair(), {'type': 'thread.started', 'thread_id': 'test'})]
        for text in inputs:
            with self.subTest(text=text):
                report = analyze(text)
                self.assertIsNone(report['metrics'])
                self.assertFalse(report['quality']['gate'])

    def test_malformed_json_variants_remain_visible(self):
        for bad in ('{"type":"user","type":"assistant"}',
                    '{"type":"assistant","value":NaN}', '{truncated', '[]'):
            with self.subTest(bad=bad):
                report = analyze(jsonl(*claude_pair()) + bad + '\n')
                self.assertEqual(report['lines']['malformed'], 1)
                self.assertFalse(report['quality']['gate'])

    def test_empty_input_is_rejected(self):
        with self.assertRaises(InputError):
            analyze(' \n')


class ExportRegression(unittest.TestCase):
    def test_projection_drops_synthetic_sensitive_content(self):
        marker = 'SYNTHETIC_PRIVATE_CANARY_9d33'
        call, result = claude_pair(True)
        block = call['message']['content'][0]
        block.update(id=marker, name=marker, input={'command': marker})
        result['message']['content'][0].update(tool_use_id=marker, content=marker)
        call.update(timestamp=marker, path=marker, unknown_field=marker)
        projected = project(jsonl(call, result))
        self.assertNotIn(marker, projected)
        self.assertEqual(projected, project(jsonl(call, result)))
        case = bundle(jsonl(call, result))
        self.assertNotIn(marker, json.dumps(case))
        self.assertTrue(case['projectionVerified'])
        self.assertTrue(verify_bundle(case)['verified'])

    def test_failure_slice_preserves_pair_and_line_mapping(self):
        call, result = claude_pair(True)
        text = jsonl({'type': 'system'}, call, result, {'type': 'summary'})
        case = bundle(text, focus='tool_failed')
        self.assertEqual(case['sourceLines'], [2, 3])
        self.assertEqual(len(case['transcript'].splitlines()), 2)
        self.assertTrue(verify_bundle(case)['verified'])

    def test_transcript_tampering_is_rejected(self):
        case = bundle(jsonl(*claude_pair()))
        case['transcript'] += '\n'
        with self.assertRaises(InputError):
            verify_bundle(case)

    def test_expected_signature_tampering_fails_verification(self):
        case = copy.deepcopy(bundle(jsonl(*claude_pair())))
        case['expected']['metrics']['toolCalls'] = 999
        self.assertFalse(verify_bundle(case)['verified'])

    def test_bundle_checks_expose_unverifiable_origin(self):
        result = verify_bundle(bundle(jsonl(*claude_pair())))
        self.assertTrue(result['bundleChecksPassed'])
        self.assertEqual(result['checks']['sourceAuthenticity'], 'not-verifiable')
        self.assertEqual(result['checks']['privacy'], 'not-verified')
        self.assertEqual(result['checks']['sourceLineAccuracy'], 'not-verifiable')

    def test_metadata_changes_do_not_masquerade_as_full_validation(self):
        base = bundle(jsonl(*claude_pair()))
        changes = [('parserVersion', '999.0'), ('projectionVerified', False),
                   ('sourceLines', [9]), ('sourceLines', [2, 1]),
                   ('sourceLines', [True, 2])]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                case = copy.deepcopy(base)
                case[key] = value
                result = verify_bundle(case)
                # Replay remains comparable, but the broader local checks fail.
                self.assertTrue(result['verified'])
                self.assertFalse(result['bundleChecksPassed'])

    def test_invalid_focus_is_rejected(self):
        with self.assertRaises(InputError):
            bundle(jsonl(*claude_pair()), focus='not-a-finding')


class CliRegression(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'incidentlab', *args],
                              text=True, capture_output=True, timeout=10)

    def test_gate_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.jsonl'
            for failed, expected in ((False, 0), (True, 2)):
                with self.subTest(failed=failed):
                    path.write_text(jsonl(*claude_pair(failed)), encoding='utf-8')
                    result = self.run_cli('inspect', str(path), '--gate')
                    self.assertEqual(result.returncode, expected, result.stderr)
                    self.assertIn('quality', json.loads(result.stdout))

    def test_verify_cli_fails_inconsistent_metadata(self):
        case = bundle(jsonl(*claude_pair()))
        case['projectionVerified'] = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic-case.json'
            path.write_text(json.dumps(case), encoding='utf-8')
            result = self.run_cli('verify', str(path))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(json.loads(result.stdout)['bundleChecksPassed'])


if __name__ == '__main__':
    unittest.main()
