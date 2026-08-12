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
- the ionic-liquid similarity API builds its Morgan index from the loaded
  public SQLite records and returns a result.

## Paper Asset Reproduction

For paper-data reproduction:

1. Verify SHA256 checksums for the CSV assets listed in `data/public_manifest.json`.
2. Import the public CSV files from `data/public/` or load the bundled demo path
   first for a smaller smoke test.
3. Extract the public model archive at the repository root. Docker does this
   during image build:

   ```bash
   tar -xzf release_assets/cemp_public_model_assets.tar.gz -C .
   ```

   If ionic-liquid model files are placed outside `ionic_liquid/static/model`,
   set `CEMP_IL_MODEL_DIR` to the extracted model directory. Use
   `CEMP_POLYMER_MODEL_DIR` for polymer models stored outside
   `polymer/static/model`.
4. Run the documented figure/table reproduction scripts.
5. Confirm table baselines listed in `docs/data.md`.

## Optional Compute Workflows

The 118 workflow notebooks, their execution functions, and their required input
order are listed in `docs/algorithms.md`. AutoCompute copies the shared
`cemp_software_settings.py` module into each task directory before notebook
execution. Configure only the external programs required by the selected
workflow using the `CEMP_*` variables in `.env.example`.

ORCA, Gaussian 16, GROMACS, Sobtop, Multiwfn, Open Babel, Open MPI, and VMD are
not bundled. Core public reproduction uses public data, model assets, and
precomputed records. Gaussian 16 requires a separately obtained valid license;
all other external programs must be installed and used under their respective
upstream terms.

Static workflow validation does not require these external programs:

```bash
python manage.py verify_public_release --manifest data/public_manifest.json
```

The verifier checks all 123 public notebooks, their syntax and cleared output
state, the exact allowlist, imported helper modules, and shared configuration.
Run a real QC or MD smoke test only on a machine that has the selected external
software and any required license.

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
