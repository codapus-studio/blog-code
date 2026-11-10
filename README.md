# Blog Code

Companion code, reproducible experiments, and recorded results for articles by Sotiris Zacharopoulos on AI, platform engineering, and architecture.

Website: [blog.codapus.studio](https://blog.codapus.studio)

Each project lives in a folder named after its article slug. Projects include their own setup instructions, inputs, and validation steps so you can explore an example without recreating the author's development environment.

## Experiments

| Article | Code | What it explores |
|---|---|---|
| Semantic Search Found the Playbook—but Missed the “Not” | [semantic-search-playbook-retrieval-negation](./semantic-search-playbook-retrieval-negation/) | Phrase matching versus semantic retrieval, including paraphrases, negation, and when to return no match |

## Getting started

Open the README in the experiment you want to run. Requirements vary by project; the playbook retrieval experiment requires Docker with Linux containers and Docker Compose v2.

```sh
cd semantic-search-playbook-retrieval-negation
docker compose build
docker compose run --rm experiment
```

The first build downloads dependencies and model weights. Evaluation runs locally with networking disabled and writes its outputs into the experiment's `results/` directory.

## Repository organisation

```text
.
├── README.md
├── .gitignore
└── semantic-search-playbook-retrieval-negation/
    ├── README.md
    ├── Dockerfile
    ├── compose.yaml
    ├── requirements.lock
    ├── download_model.py
    ├── experiment.py
    ├── verify_results.py
    ├── cases.json
    ├── baseline/
    ├── recorded-results/
    └── results/
```

`recorded-results/` contains the evidence used in the article. `results/` holds outputs from subsequent local runs and is excluded from version control, apart from its placeholder file.

## Reading the results

These examples are learning experiments. Their READMEs distinguish measured results from assumptions and describe the limits of each comparison. Synthetic examples do not establish production readiness or imply production deployment experience.

Where an experiment uses a model, its configuration and provenance are recorded. Follow the project README for reproduction details and any expected numerical tolerance.

## Reporting issues

If you find a problem, include the experiment folder, command you ran, relevant runtime versions, and the observed error. Remove credentials and private data from logs before sharing them.

Suggestions that improve clarity, reproducibility, or evaluation quality are welcome.
