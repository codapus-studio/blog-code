"""Authored teaching experiment. No production data, generation, or remediation."""
import csv
import hashlib
import importlib.util
import json
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

OUT = Path('/results')
OUT.mkdir(exist_ok=True)
LEGACY = Path(__file__).resolve().parent / 'baseline'
spec = importlib.util.spec_from_file_location('original_baseline', LEGACY / 'baseline.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
corpus = json.loads((LEGACY / 'corpus.json').read_text())
authored = json.loads(Path('cases.json').read_text())
splits = {split: [dict(id=i, category=c, query=q, expected=e) for i, c, q, e in rows]
          for split, rows in authored.items()}
splits['original'] = [dict(id=c['id'], category=c['group'], query=c['query'], expected=c['expected_document_id'])
                      for c in json.loads((LEGACY / 'cases.json').read_text())]
ids = [d['id'] for d in corpus]
assert len(ids) == len(set(ids)) == 3
assert not ({c['query'].strip().casefold() for c in splits['development']} &
            {c['query'].strip().casefold() for c in splits['test']} - {''})
for split, cases in splits.items():
    assert len({c['id'] for c in cases}) == len(cases)
    assert all(c['expected'] in ids + [None] for c in cases)

torch.set_num_threads(2)
torch.manual_seed(0)
model = SentenceTransformer('/opt/model', device='cpu', local_files_only=True)
# The model sees title + body only, never the expected labels or matching phrases.
documents = [d['title'] + '. ' + d['body'] for d in corpus]
doc_vectors = model.encode(documents, normalize_embeddings=True, convert_to_numpy=True)

def score(cases):
    vectors = model.encode([c['query'] for c in cases], normalize_embeddings=True, convert_to_numpy=True)
    matrix = vectors @ doc_vectors.T
    result = []
    for c, values in zip(cases, matrix):
        ranking = np.argsort(-values, kind='stable')
        first, second = int(ranking[0]), int(ranking[1])
        result.append({**c, 'nearest': ids[first], 'top_score': float(values[first]),
                       'margin': float(values[first] - values[second]),
                       'scores': {i: float(v) for i, v in zip(ids, values)}})
    return result

def select(row, threshold, margin):
    if not row['query'].strip() or row['top_score'] < threshold or row['margin'] < margin:
        return None
    return row['nearest']

def metrics(rows, predictions):
    positive = [i for i, r in enumerate(rows) if r['expected'] is not None]
    negative = [i for i, r in enumerate(rows) if r['expected'] is None]
    correct = sum(predictions[i] == rows[i]['expected'] for i in positive)
    abstain = sum(predictions[i] is None for i in negative)
    matched = sum(p is not None for p in predictions)
    return dict(answerable_correct=correct, answerable_total=len(positive),
                abstention_correct=abstain, abstention_total=len(negative),
                incorrect_selections=sum(p is not None and p != r['expected'] for p, r in zip(predictions, rows)),
                matches=matched, total=len(rows),
                exact_correct=sum(p == r['expected'] for p, r in zip(predictions, rows)),
                match_precision=correct / matched if matched else None,
                balanced_success=(correct / len(positive) + abstain / len(negative)) / 2)

# Fixed in advance: maximise the mean of correct-selection and correct-abstention rates.
# Ties: fewer incorrect selections, then higher score threshold, then higher margin.
# This is a teaching objective, not a production risk policy.
development = score(splits['development'])
grid = []
for threshold in np.arange(0, 1.0001, .025):
    for margin in np.arange(0, .3001, .025):
        predictions = [select(r, float(threshold), float(margin)) for r in development]
        grid.append(dict(threshold=round(float(threshold), 3), margin=round(float(margin), 3),
                         **metrics(development, predictions)))
best = max(grid, key=lambda x: (x['balanced_success'], -x['incorrect_selections'], x['threshold'], x['margin']))
policy = {'threshold': best['threshold'], 'margin': best['margin'], 'development_metrics': best,
          'objective': 'Mean of answerable success and correct abstention; ties favour fewer incorrect selections, then higher threshold, then higher margin.'}
(OUT / 'frozen-policy.json').write_text(json.dumps(policy, indent=2) + '\n')
# Only now score the test set. Never retune against these results.
scored = {'development': development, 'test': score(splits['test']), 'original': score(splits['original'])}
summary, details = {}, []
for split, rows in scored.items():
    predictions = {
        'phrase': [baseline.lookup(r['query'], corpus)['document_id'] for r in rows],
        'semantic_top1': [r['nearest'] if r['query'].strip() else None for r in rows],
        'semantic_gated': [select(r, policy['threshold'], policy['margin']) for r in rows],
    }
    summary[split] = {name: metrics(rows, values) for name, values in predictions.items()}
    for idx, row in enumerate(rows):
        details.append(dict(split=split, **row, **{name: values[idx] for name, values in predictions.items()}))

assert summary['original']['phrase']['exact_correct'] == 8, 'Original 8/11 baseline changed'
for name, m in summary['test'].items():
    assert m['answerable_total'] == m['abstention_total'] == 12
    assert 0 <= m['exact_correct'] <= m['total']
manifest = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                platform=platform.platform(), torch_threads=torch.get_num_threads(),
                model=json.loads(Path('/opt/model-source.json').read_text()),
                document_representation='title + . + body; normalized embeddings; dot product = cosine similarity',
                hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                        [Path('cases.json'), Path('experiment.py'), LEGACY/'baseline.py', LEGACY/'corpus.json', LEGACY/'cases.json']})
for name, value in [('summary', summary), ('predictions', details), ('development-grid', grid), ('manifest', manifest)]:
    (OUT / f'{name}.json').write_text(json.dumps(value, indent=2) + '\n')
shutil.copy('/opt/packages.txt', OUT / 'packages.txt')
with (OUT / 'predictions.csv').open('w', newline='') as f:
    fields = ['split', 'id', 'category', 'query', 'expected', 'nearest', 'top_score', 'margin', 'phrase', 'semantic_top1', 'semantic_gated']
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(details)
lines = ['# Retrieval experiment results', '', 'Generated by experiment.py. Counts are from authored synthetic cases, not operational traffic.', '',
         f"Frozen development policy: cosine >= {policy['threshold']:.3f}, top-two margin >= {policy['margin']:.3f}. Blank input always abstains.", '']
for split, methods in summary.items():
    lines += [f'## {split}', '', '| Method | Correct answerable | Correct abstention | Incorrect selections | Exact correct |', '|---|---:|---:|---:|---:|']
    for name, m in methods.items():
        lines.append(f"| {name} | {m['answerable_correct']}/{m['answerable_total']} | {m['abstention_correct']}/{m['abstention_total']} | {m['incorrect_selections']} | {m['exact_correct']}/{m['total']} |")
    lines += ['']
(OUT / 'results.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'policy': policy, 'summary': summary}, indent=2))
