# Reproducibility Workflow

## Local Demo Reproduction

Run the full local demo path:

```bash
python manage.py migrate
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
python manage.py verify_public_release --manifest data/public_manifest.json
python manage.py runserver
```

Then open:

```text
http://localhost:8000
```

Expected result:

- migrations finish without private configuration;
- demo CSV files load into SQLite;
- demo user and API token are created;
- `verify_public_release` passes;
- `/health/` returns `{"status": "ok"}`.

## Paper Asset Reproduction

After Zenodo/GitHub Release archival is complete:

1. Download the release assets listed in `data/public_manifest.json`.
2. Verify SHA256 checksums.
3. Load the public SQLite snapshot or import CSV/XLSX exports.
4. Extract `cemp_public_model_assets.tar.gz`; if the model files are not placed
   under `ionic_liquid/static/model`, set `CEMP_IL_MODEL_DIR` to the extracted
   model directory.
5. Run the documented figure/table reproduction scripts.
6. Confirm table-row baselines listed in `docs/data.md`.

The paper asset DOI is `TBD` until archival is completed.

## Optional Compute Workflows

ORCA, Gaussian, GROMACS, and Multiwfn workflows are optional. Core public
reproduction uses public data, model assets, and precomputed records. If a
researcher enables optional compute workflows, they must install and license
the relevant external tools independently.

## Release Gate

Before tagging a manuscript release:

```bash
python -m compileall -q .
python manage.py check
python manage.py test
python manage.py verify_public_release --manifest data/public_manifest.json
```

If the frontend changes:

```bash
cd crystals/frontend
npm ci
npm run build
```
