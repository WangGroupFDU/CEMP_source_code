# CEMP: Clean Energy Materials Platform

CEMP is a Django-based clean energy materials platform for database browsing,
materials query APIs, machine-learning prediction workflows, and optional
computational chemistry workflow orchestration.

This repository is the open-source `main` release for the manuscript-associated
CEMP platform. The source code is released under Apache-2.0. Public demo data,
public data manifests, public data dictionaries, and public data/model assets are
released under CC BY 4.0 unless a specific manifest entry states otherwise.

## Quick Start

### Docker

```bash
git clone https://github.com/WangGroupFDU/CEMP_source_code.git
cd CEMP_source_code
docker compose up --build
```

The container runs migrations, loads the bundled demo data, creates the demo
account, and starts Django at:

```text
http://localhost:8000
```

Demo credentials:

```text
username: cemp_demo
password: cemp_demo_local
```

### Conda

```bash
git clone https://github.com/WangGroupFDU/CEMP_source_code.git
cd CEMP_source_code
mamba env create -f environment.yml
conda activate cemp-public
python manage.py migrate
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
python manage.py runserver
```

## Repository Layout

| Path | Purpose |
| --- | --- |
| `cemp/` | Django project settings, URL routing, ASGI/WSGI entry points. |
| `home/` | Landing pages, API-token page, public release management commands. |
| `register/` | User registration, demo profile setup, permission flags. |
| `ionic_liquid/` | Ionic-liquid database models, query APIs, prediction helpers. |
| `polymer/` | Polymer database models, generation workflows, prediction utilities. |
| `crystals/` | Crystal/material models, optional Materials Project fetch script, prediction code. |
| `battery_manage_system/` | Battery experiment models, visualization and prediction views. |
| `autocompute/` | Optional QC/MD workflow orchestration and task-management modules. |
| `data/demo/` | Small local demo CSV assets for smoke tests and API examples. |
| `data/public/` | Public GitHub CSV assets, including Autocompute small molecules and polymer ML predictions. |
| `data/public_manifest.json` | Versioned data/model manifest, checksums, licenses, and release pointers. |
| `docs/` | Installation, data, API, reproducibility, and availability notes. |

## Public Data and Models

The repository stores demo CSV files and public database CSV assets directly in
GitHub where file size permits. Model artifacts that are not suitable as regular
repository files can be attached to the GitHub Release. The manifest records the
expected public snapshot baseline.
Experimental or theoretical calculation datasets are counted as data points; ML
datasets are counted as rows.

| Public table | Count type | Expected count |
| --- | --- | ---: |
| `ionic_liquid_il` | data points | 1,065 |
| `ionic_liquid_il_ml_data` | rows | 100,000 |
| `ionic_liquid_cation_qc_data` | data points | 3,774 |
| `ionic_liquid_anion_qc_data` | data points | 2,220 |
| `polymer_experiment_polymer_data` | data points | 13,116 |
| `polymer_calculated_monomer_data` | data points | 10,519 |
| `polymer_calculated_polymer_data` | data points | 1,000 |
| `battery_manage_system_bms_experiment_result` | data points | 39 |

Additional GitHub CSV assets in `data/public/` include the full public paper
database tables, Autocompute small-molecule database exports, and `213,581` rows
of ML-predicted OMG polymer properties.

## Local Release Commands

```bash
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
python manage.py verify_public_release --manifest data/public_manifest.json
```

`load_public_data` imports bundled demo CSV assets into SQLite. `seed_public_demo`
creates a local demo user and token. `verify_public_release` checks local demo
files, SHA256 values, count metadata, and release-language constraints.

## API Example

After starting Django and seeding the demo user:

```bash
curl -X POST http://localhost:8000/api/token/ \
  -d "username=cemp_demo" \
  -d "password=cemp_demo_local"
```

Use the returned token for authenticated endpoints. Public API notes are in
`docs/api.md`.

## Optional Scientific Software

The AutoCompute modules include workflow templates for ORCA, Gaussian, GROMACS,
and Multiwfn. These tools have separate installation and license requirements.
They are optional for the public demo path. The bundled reproducibility checks
use public data, public model artifacts, and precomputed records.

Materials Project refresh scripts require a user-provided API key through
`MP_API_KEY`. No API key is stored in this repository.

## Validation

Recommended checks before publishing a release:

```bash
python -m compileall -q .
python manage.py check
python manage.py test
python manage.py verify_public_release --manifest data/public_manifest.json
```

If the Vue frontend under `crystals/frontend/` is changed:

```bash
cd crystals/frontend
npm ci
npm run build
```

## Citation

Use `CITATION.cff` for software citation metadata. After the manuscript release
is finalized, update the manuscript reference and release tag if needed.

## Licenses

- Source code: Apache-2.0, see `LICENSE`.
- Public data and data/model assets: CC BY 4.0, see `DATA_LICENSE` and
  `data/public_manifest.json`.
