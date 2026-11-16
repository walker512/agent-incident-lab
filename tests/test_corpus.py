"""Offline source-derived regressions. Expectations are reviewed raw-field labels."""
import hashlib
import json
from pathlib import Path
import unittest

from incidentlab.core import analyze, bundle, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'tests/corpus/manifest.json').read_text())


class PublicCorpusRegression(unittest.TestCase):
    def test_provenance_and_run_denominator(self):
        cases = MANIFEST['cases']
        self.assertEqual(len({c['id'] for c in cases}), len(cases))
        real = [c for c in cases if c['classification'] == 'public-real-run']
        self.assertEqual(len({c['independent_run_id'] for c in real}), 1)
        for c in cases:
            self.assertIn(c['classification'], {'controlled-real-run', 'public-real-run',
                                               'upstream-fixture', 'synthetic'})
            self.assertIn('76f1b5129b974afdf8e59e4ae3755083c10ff8ff', c['source_url'])
            self.assertIn('MIT License', (ROOT / c['license_notice']).read_text())
            self.assertTrue(c['privacy_review'])
            self.assertTrue(c['producer_version'])
            if c['classification'] == 'upstream-fixture':
                self.assertIsNone(c['independent_run_id'])

    def test_fixed_labels_against_projected_artifacts(self):
        for c in MANIFEST['cases']:
            with self.subTest(case=c['id']):
                raw = (ROOT / c['artifact']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), c['artifact_sha256'])
                report = analyze(raw.decode('utf-8'))
                e, m = c['expected'], report['metrics']
                self.assertEqual(report['format'], e['format'])
                self.assertEqual(report['lines']['total'], e['records'])
                self.assertEqual(report['lines']['malformed'], 0)
                self.assertEqual(m['toolCalls'], e['calls'])
                self.assertEqual(m['toolResults'], e['results'])
                self.assertEqual(m['failedTools'], e['failures'])
                self.assertEqual(m['pendingTools'], 0)
                self.assertEqual(m['unknownOutcomes'], e['unknown_outcomes'])
                self.assertEqual(report['quality']['gate'], e['gate'])
                self.assertEqual([r['line'] for r in report['ledger']
                                  if r['status'] == 'unknown'], e['unknown_lines'])
                for a in c['annotations']:
                    matches = [call for call in report['calls']
                               if (call['line'], call['resultLine']) ==
                               (a['call_line'], a['result_line'])]
                    self.assertEqual(len(matches), 1)
                    self.assertEqual(matches[0]['status'], a['status'])
                failures = sorted((call['line'], call['resultLine'])
                                  for call in report['calls'] if call['status'] == 'failed')
                self.assertEqual(failures, sorted((a['call_line'], a['result_line'])
                                 for a in c['annotations'] if a['status'] == 'failed'))
                self.assertTrue(verify_bundle(bundle(raw.decode()))['bundleChecksPassed'])

    def test_claude_failure_slice_keeps_exact_reviewed_pairs(self):
        c = MANIFEST['cases'][0]
        case = bundle((ROOT / c['artifact']).read_text(), focus='tool_failed')
        expected = sorted(n for a in c['annotations'] if a['status'] == 'failed'
                          for n in (a['call_line'], a['result_line']))
        self.assertEqual(case['sourceLines'], expected)
        self.assertEqual(len(case['transcript'].splitlines()), 10)
        self.assertTrue(verify_bundle(case)['bundleChecksPassed'])


class CapturedFragmentCoverageRegression(unittest.TestCase):
    def test_successful_edit_fragment_remains_an_explicit_coverage_gap(self):
        meta = json.loads((ROOT / 'tests/corpus/gascity-provenance.json').read_text())
        raw = (ROOT / 'tests/corpus/gascity-edit.jsonl').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), meta['artifact_sha256'])
        report = analyze(raw.decode())
        self.assertEqual(report['lines']['recognized'], 2)
        self.assertEqual([r['line'] for r in report['ledger'] if r['status'] == 'unknown'], [3])
        self.assertEqual(report['metrics']['toolCalls'], 1)
        self.assertEqual(report['metrics']['toolResults'], 0)
        self.assertEqual(report['metrics']['pendingTools'], 1)
        self.assertEqual(report['metrics']['failedTools'], 0)
        self.assertFalse(report['quality']['gate'])
        self.assertEqual({f['code'] for f in report['findings']},
                         {'missing_result', 'unrecognized_records'})
        # This locks transparent reporting of a limitation, not correct correlation.
        self.assertEqual(meta['raw_annotation']['result_line'], 3)
