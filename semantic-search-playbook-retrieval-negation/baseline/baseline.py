"""Offline teaching baseline. No model calls and no remediation actions."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lookup(query, corpus):
    normalized = query.casefold()
    matches = [doc['id'] for doc in corpus if any(term in normalized for term in doc['phrases'])]
    if len(matches) == 1:
        return {'status': 'match', 'document_id': matches[0]}
    return {'status': 'abstain', 'document_id': None}


def main():
    corpus = json.loads((HERE / 'corpus.json').read_text(encoding='utf-8'))
    cases = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))
    results = []
    for case in cases:
        actual = lookup(case['query'], corpus)
        expected = {'status': case['expected_status'], 'document_id': case['expected_document_id']}
        results.append({**case, 'actual': actual, 'passed': actual == expected})
    (HERE / 'baseline-results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    for group in sorted({case['group'] for case in cases}):
        subset = [row for row in results if row['group'] == group]
        print(f"{group}: {sum(row['passed'] for row in subset)}/{len(subset)}")


if __name__ == '__main__':
    main()
