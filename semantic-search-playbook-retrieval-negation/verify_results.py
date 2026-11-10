"""Independently recount saved decisions without importing the experiment or ML stack."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--results', type=Path, default=Path('/results'))
parser.add_argument('--reference', type=Path)
args = parser.parse_args()
root = args.results
rows = json.loads((root / 'predictions.json').read_text())
summary = json.loads((root / 'summary.json').read_text())
policy = json.loads((root / 'frozen-policy.json').read_text())
for split, methods in summary.items():
    subset = [r for r in rows if r['split'] == split]
    for method, recorded in methods.items():
        answerable = [r for r in subset if r['expected'] is not None]
        unsupported = [r for r in subset if r['expected'] is None]
        assert recorded['answerable_correct'] == sum(r[method] == r['expected'] for r in answerable)
        assert recorded['abstention_correct'] == sum(r[method] is None for r in unsupported)
        assert recorded['incorrect_selections'] == sum(r[method] is not None and r[method] != r['expected'] for r in subset)
        assert recorded['exact_correct'] == sum(r[method] == r['expected'] for r in subset)
        assert recorded['total'] == len(subset)
for row in rows:
    eligible = bool(row['query'].strip()) and row['top_score'] >= policy['threshold'] and row['margin'] >= policy['margin']
    assert row['semantic_gated'] == (row['nearest'] if eligible else None)
    values = sorted(row['scores'].values(), reverse=True)
    assert abs(row['top_score'] - values[0]) < 1e-7
    assert abs(row['margin'] - (values[0] - values[1])) < 1e-6
assert summary['original']['phrase']['exact_correct'] == 8
if args.reference:
    reference_summary = json.loads((args.reference / 'summary.json').read_text())
    reference_rows = json.loads((args.reference / 'predictions.json').read_text())
    reference_policy = json.loads((args.reference / 'frozen-policy.json').read_text())
    assert summary == reference_summary, 'Summary differs from the article evidence'
    assert policy == reference_policy, 'Selected policy differs from the article evidence'
    assert len(rows) == len(reference_rows)
    for actual, reference in zip(rows, reference_rows):
        for field in ['split', 'id', 'query', 'expected', 'phrase', 'semantic_top1', 'semantic_gated']:
            assert actual[field] == reference[field], f'Decision changed: {actual["id"]} {field}'
        for field in ['top_score', 'margin']:
            assert abs(actual[field] - reference[field]) < 1e-5, f'Score changed: {actual["id"]}'
    print('PASS: results reproduce the article evidence (score tolerance 0.00001).')
print(f'PASS: independent counts and frozen-policy decisions verified for all {len(rows)} cases across three methods.')
