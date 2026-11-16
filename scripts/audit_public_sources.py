"""Explicit opt-in audit of pinned public sources; never reads session directories.

Does not import incidentlab: raw evidence checks are independent of the parser.
No raw content is saved or printed. Network errors and mismatches fail closed.
"""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def check(condition, description):
    if not condition:
        raise ValueError(description)


def audit(c, raw):
    check(len(raw) == c['source_bytes'], 'source size changed')
    check(hashlib.sha256(raw).hexdigest() == c['source_sha256'], 'source hash changed')
    rows = [json.loads(line) for line in raw.splitlines()]
    check(len(rows) == c['expected']['records'], 'record count changed')
    calls, results, unknown = {}, {}, []
    for n, row in enumerate(rows, 1):
        if c['expected']['format'] == 'claude':
            content = row.get('message', {}).get('content', [])
            if not isinstance(content, list):
                continue
            for block in content:
                if block.get('type') == 'tool_use':
                    key = block['id']
                    check(key not in calls, 'duplicate call ID')
                    calls[key] = n
                elif block.get('type') == 'tool_result':
                    key = block['tool_use_id']
                    check(key not in results, 'duplicate result ID')
                    results[key] = (n, 'failed' if block.get('is_error') is True else 'success')
        elif c['expected']['format'] == 'codex-session':
            p = row['payload']
            if row['type'] == 'response_item' and p['type'] == 'function_call':
                check(p['call_id'] not in calls, 'duplicate call ID')
                calls[p['call_id']] = n
            elif row['type'] == 'response_item' and p['type'] == 'function_call_output':
                check(isinstance(p['output'], str), 'expected opaque output')
                check(p['call_id'] not in results, 'duplicate result ID')
                results[p['call_id']] = (n, 'unknown')
            if row['type'] == 'event_msg' and p['type'] == 'task_completed':
                unknown.append(n)
        elif row['type'] in ('item.started', 'item.completed'):
            item = row['item']
            if item['type'] == 'command_execution':
                key = item['id']
                if row['type'] == 'item.started':
                    check(key not in calls, 'duplicate call ID')
                    calls[key] = n
                else:
                    check(type(item['exit_code']) is int, 'expected integer exit code')
                    check(key not in results, 'duplicate result ID')
                    results[key] = (n, 'failed' if item['exit_code'] else 'success')
    e = c['expected']
    check(len(calls) == e['calls'] and len(results) == e['results'], 'call/result count mismatch')
    check(calls.keys() == results.keys(), 'unpaired source IDs')
    check(sum(status == 'failed' for _, status in results.values()) == e['failures'], 'failure count mismatch')
    check(sum(status == 'unknown' for _, status in results.values()) == e['unknown_outcomes'], 'unknown outcome mismatch')
    check(unknown == e['unknown_lines'], 'unknown event lines mismatch')
    by_hash = {hashlib.sha256(key.encode()).hexdigest(): (calls[key], *result)
               for key, result in results.items()}
    for a in c['annotations']:
        check(by_hash.get(a['call_id_sha256']) ==
              (a['call_line'], a['result_line'], a['status']), 'reviewed pair mismatch')
    if e['format'] == 'claude':
        check({r['version'] for r in rows if 'version' in r} == {c['producer_version']}, 'version mismatch')
    elif e['format'] == 'codex-session':
        check(rows[0]['payload']['cli_version'] == c['producer_version'], 'fixture version mismatch')


def main():
    manifest = json.loads((ROOT / 'tests/corpus/manifest.json').read_text())
    for case in manifest['cases']:
        # URLs are pinned, reviewed repository data, not user-supplied log locations.
        with urllib.request.urlopen(case['source_url'], timeout=30) as response:
            raw = response.read(2 * 1024 * 1024)
        audit(case, raw)
        print(case['id'] + ': pinned source hash and independent raw-field labels PASS')
    meta = json.loads((ROOT / 'tests/corpus/gascity-provenance.json').read_text())
    with urllib.request.urlopen(meta['source_url'], timeout=30) as response:
        raw = response.read(2 * 1024 * 1024)
    check(hashlib.sha256(raw).hexdigest() == meta['source_sha256'], 'Gas City source hash changed')
    rows = [json.loads(line) for line in raw.splitlines()]
    check(len(rows) == 3, 'Gas City record count changed')
    call = rows[1]['message']['content'][0]
    result = rows[2]['message']['content'][0]
    check(rows[2]['type'] == 'tool_result', 'expected unsupported top-level result')
    check(call['id'] == result['tool_use_id'], 'Gas City pair mismatch')
    check(hashlib.sha256(call['id'].encode()).hexdigest() ==
          meta['raw_annotation']['call_id_sha256'], 'Gas City ID hash mismatch')
    check(call['name'] == 'Edit' and result.get('is_error', False) is False,
          'Gas City negative control changed')
    print('gascity-edit-fragment: raw success pair PASS; parser coverage gap remains')
    print('Full public real runs: 1; sanitized capture fragments: 1; upstream fixtures: 2.')
    print('Upstream-described authenticity, not independently witnessed; not diagnostic accuracy.')


if __name__ == '__main__':
    main()
