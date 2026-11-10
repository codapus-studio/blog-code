# Semantic search found the playbook—but missed the “not”

Companion experiment for the article **Semantic Search Found the Playbook—but Missed the “Not”**. The article slug and project name are `semantic-search-playbook-retrieval-negation`.

This self-contained teaching experiment compares a literal phrase matcher with an embedding model. It uses three fictional playbooks and tests both finding an applicable entry and returning no match. It does not generate mitigation instructions or perform production actions.

## Run it

Requires Docker with Linux containers and Docker Compose v2. No host Python installation, GPU, credentials, or inference API subscription is required. Run these commands from this folder on Windows, macOS, or Linux:

```sh
docker compose build
docker compose run --rm experiment
```

The build downloads public Python packages and a pinned model revision. Allow several GB of disk space. The experiment itself runs offline, using two CPUs and at most 2 GB of memory. The image targets Linux amd64; other architectures may use Docker emulation.

Results are written to `results/`. Each run overwrites those generated files. The original article evidence in `recorded-results/` stays unchanged. The default command also verifies the new results against that evidence and exits with an error if decisions, counts, policy, or scores outside a 0.00001 tolerance differ.

Verify the original evidence without rerunning inference:

```sh
docker compose run --rm experiment python verify_results.py --results /app/recorded-results
```

When deliberately changing cases or the algorithm, run without the original-evidence comparison, then check the new results internally:

```sh
docker compose build
docker compose run --rm experiment python experiment.py
docker compose run --rm experiment python verify_results.py
```

The original eleven-case baseline regression check still applies. Preserve the published evidence rather than replacing it with new experiments.

## Results used in the article

| Method | Correct answers / 12 answerable | Correct abstentions / 12 no-match | Incorrect selections |
|---|---:|---:|---:|
| Literal phrase matcher | 6/12 | 9/12 | 3 |
| Semantic nearest entry | 12/12 | 1/12 | 11 |
| Semantic with rejection rules | 9/12 | 10/12 | 2 |

All methods abstain on blank input. Ungated semantic search otherwise always returns the nearest entry, so its poor abstention is a result of that return policy. Its top-ranked candidate was correct on all twelve answerable cases.

One rejected symptom still passed the semantic gates:

> The certificate has not expired; the error is a missing DNS record.

The certificate playbook received a cosine similarity of about 0.688 and a lead of 0.608 over the next candidate. Both exceeded the selected cutoffs. Similarity was not sufficient evidence of applicability.

## Method

- `baseline/` contains the original unchanged matcher, corpus, and eleven regression cases. IDs retain their original `rb-` prefix; these map to the article's `pb-` entries by number.
- `cases.json` adds 24 development and 24 test cases, authored before the original run. Each split contains twelve supported requests and twelve no-match requests.
- Cases include direct phrases, paraphrases, unsupported topics, blank input, negation, background mentions, multiple symptoms, and underspecified requests. Multiple supported symptoms are labelled no-match under the single-result contract.
- `all-MiniLM-L6-v2` embeds document title plus body and query text. Normalized vectors are compared using their dot product, equivalent to cosine similarity. Labels and baseline trigger phrases are not embedded.
- A development-only grid search considers score thresholds from 0 to 1 and top-two margins from 0 to 0.3, both in 0.025 steps. It maximises the mean of correct-answer and correct-abstention rates. Ties favour fewer incorrect selections, then higher threshold, then higher margin.
- The resulting score threshold is 0.575 and minimum margin is 0.275. The policy is saved before scoring test cases; the test cases do not influence selection.
- The original eleven-case phrase baseline remains 8/11 correct.

The principal lesson is a trade-off: semantic ranking recovers paraphrases, while rejection rules prevent many irrelevant results but also discard useful answers. The chosen thresholds are specific to this exercise.

## Reproducibility and evidence

The base image digest, full resolved Python package versions, and model revision are pinned. This provides a reproducible configuration, not a guarantee of bit-identical floating-point results across hardware. Model weights are downloaded into the image, not committed to the repository. `requirements.lock` pins versions; it is not a package-hash lockfile.

The original evidence was generated on 10 November 2026. Its manifest records the original runtime paths and source hashes. Packaging changes relocate the baseline inside this project and add verification, so a new run's source hashes and timestamp will differ. The verifier compares results rather than expecting those provenance fields to match.

| File | Purpose |
|---|---|
| `experiment.py` | Retrieval, threshold selection, metrics, and report generation |
| `verify_results.py` | Independent recount, policy checks, and optional comparison with original evidence |
| `cases.json` | New labelled development and test requests |
| `baseline/` | Original phrase matcher, corpus, and regression cases |
| `recorded-results/results.md` | Original count tables |
| `recorded-results/predictions.csv` | Every original query and prediction |
| `recorded-results/predictions.json` | Full-precision scores and predictions |
| `recorded-results/manifest.json` | Original runtime, timestamp, model revision, and input hashes |
| `recorded-results/development-grid.json` | All development configurations |
| `results/` | Generated outputs from your own run |

## Limits

This is an assistant-assisted synthetic experiment, not production experience. The development and test splits share an author and related templates; they are not independently sourced incident traffic. The small grid search can overfit. The baseline is literal phrase matching, not BM25 or all lexical retrieval, and uses different document information from the embedding approach. No permissions, freshness enforcement, latency, costs, or engineer time savings were evaluated.

After using these failures to guide changes, use fresh independently labelled cases to assess improvement.

## References

- [Model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [Sentence Transformers: semantic textual similarity](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)

Model weights and dependencies retain their respective licences. See the model card for its licence and intended use.
