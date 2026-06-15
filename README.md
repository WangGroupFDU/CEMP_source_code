# CEMP: Clean Energy Materials Platform

CEMP is a Django-based clean energy materials platform for database browsing,
materials query APIs, machine-learning prediction workflows, and optional
computational chemistry workflow orchestration.

This repository contains the public release of the CEMP platform associated with
the manuscript. The source code is released under Apache-2.0. Public demo data,
data manifests, data dictionaries, and data/model assets are released under CC BY
4.0 unless a specific manifest entry states otherwise.

## Quick Start

### Docker

```bash
git clone https://github.com/WangGroupFDU/CEMP_source_code.git
cd CEMP_source_code
cp .env.example .env
docker compose up --build
```

The container runs migrations, loads the bundled demo data, creates the demo
account, and starts Django at:

```text
http://localhost:8000
```

On a shared server, choose a free host port and update `.env`, for example
`CEMP_HOST_PORT=18080`. If Docker bridge networking fails on CentOS, use the
host-network Compose file documented in `docs/deploy.md`.

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

## Database Files and Locations

CEMP stores the public database snapshots as CSV files in this repository. The
Django runtime database is created locally from those CSV files; a production
database dump is not committed.

### Runtime Database

| Environment | Database location | Notes |
| --- | --- | --- |
| Docker demo | `/app/public_demo.sqlite3` inside the container | Controlled by `CEMP_SQLITE_PATH` in `.env`; the default is shown in `.env.example`. |
| Local Conda demo | `<repo>/public_demo.sqlite3` | Used when `CEMP_SQLITE_PATH` is not set. |
| Custom SQLite path | Any path assigned to `CEMP_SQLITE_PATH` | Useful when keeping the database outside the source tree. |
| Optional MySQL | Configured through `CEMP_ENABLE_MYSQL=true` and `CEMP_MYSQL_*` | Disabled by default; not required for the public demo. |

### CSV Source Files

| Dataset group | GitHub location | Default local import | Notes |
| --- | --- | --- | --- |
| Demo database | `data/demo/*.csv` | Yes, with `--mode demo` | Small records used by Quick Start, API examples, and smoke tests. |
| Paper public database | `data/public/paper_*.csv` | No, use `--mode paper` | Public CSV snapshots supporting the manuscript data tables. |
| Autocompute small-molecule database | `data/public/autocompute_*.csv` | No, use `--mode paper` for the paper-linked subset | CSV exports corresponding to the public database pages under `/autocompute/Database`. |
| OMG polymer ML predictions | `data/public/polymer_predicted_omg_deepsa_cemp_property.csv` | No | File-based public asset with 213,581 ML prediction rows. |
| Release manifest | `data/public_manifest.json` | Read by loader and verifier | Records paths, SHA256 checksums, licenses, count metadata, and release grouping. |

The default Quick Start path imports only `data/demo/` into the local SQLite
database. The larger public CSV files remain directly available under
`data/public/`. To import the paper-linked CSV assets into SQLite, run:

```bash
python manage.py load_public_data --manifest data/public_manifest.json --mode paper
```

By default, `load_public_data` replaces records in the target models before
loading each CSV. Add `--append` only when intentionally merging with an
existing local database.

The Autocompute ionic-liquid CSV and the paper ionic-liquid CSV describe the
same public ionic-liquid table under different release contexts, so the paper
loader imports the paper CSV and leaves the Autocompute-named copy as a file
asset for web-database traceability.

### Public Web Database Mapping

The public small-molecule database pages under `/autocompute/Database` map to
the following GitHub CSV files:

| Web database page | GitHub CSV | Django model |
| --- | --- | --- |
| `/autocompute/Database/Cation` | `data/public/autocompute_cation_qc.csv` | `ionic_liquid.Cation` |
| `/autocompute/Database/Anion` | `data/public/autocompute_anion_qc.csv` | `ionic_liquid.Anion` |
| `/autocompute/Database/IL` | `data/public/autocompute_ionic_liquid_qc.csv` | `ionic_liquid.IL` |
| `/autocompute/Database/electrolyte` | `data/public/autocompute_electrolyte_qc.csv` | `ionic_liquid.electrolyte` |
| `/autocompute/Database/Li_electrolyte` | `data/public/autocompute_li_electrolyte_qc.csv` | `ionic_liquid.Li_electrolyte` |
| `/autocompute/Database/Salt` | `data/public/autocompute_metal_anion_binding_energy.csv` | `ionic_liquid.metal_anion_energy` |
| `/autocompute/Database/example` | `data/public/autocompute_example_small_molecules.csv` | `ionic_liquid.Example` |

## Public Data and Models

The repository includes demo CSV files and public database CSV assets directly
where file size permits. Larger model artifacts can be attached to the GitHub
Release. The manifest records the expected public snapshot baseline.
Experimental datasets are counted as measured property data points. Quantum
chemistry tables and ML-generated datasets are reported as rows.

| Public asset | GitHub location | Count type | Expected count |
| --- | --- | --- | ---: |
| `paper_ionic_liquid_il` | `data/public/paper_ionic_liquid_il.csv` | rows | 1,065 |
| `paper_ionic_liquid_il_ml_data` | `data/public/paper_ionic_liquid_il_ml_data.csv` | rows | 100,000 |
| `paper_ionic_liquid_cation_qc_data` | `data/public/paper_ionic_liquid_cation_qc_data.csv` | rows | 3,774 |
| `paper_ionic_liquid_anion_qc_data` | `data/public/paper_ionic_liquid_anion_qc_data.csv` | rows | 2,220 |
| `paper_polymer_experiment_polymer_data` | `data/public/paper_polymer_experiment_polymer_data.csv` | data points | 21,402 |
| `paper_polymer_calculated_monomer_data` | `data/public/paper_polymer_calculated_monomer_data.csv` | rows | 10,519 |
| `paper_polymer_calculated_polymer_data` | `data/public/paper_polymer_calculated_polymer_data.csv` | rows | 1,000 |
| `polymer_predicted_omg_deepsa_cemp_property` | `data/public/polymer_predicted_omg_deepsa_cemp_property.csv` | rows | 213,581 |
| `paper_bms_experiment_result` | `data/public/paper_bms_experiment_result.csv` | data points | 39 |
| `autocompute_cation_qc` | `data/public/autocompute_cation_qc.csv` | rows | 431 |
| `autocompute_anion_qc` | `data/public/autocompute_anion_qc.csv` | rows | 63 |
| `autocompute_ionic_liquid_qc` | `data/public/autocompute_ionic_liquid_qc.csv` | rows | 1,065 |
| `autocompute_electrolyte_qc` | `data/public/autocompute_electrolyte_qc.csv` | rows | 1,397 |
| `autocompute_li_electrolyte_qc` | `data/public/autocompute_li_electrolyte_qc.csv` | rows | 4,197 |
| `autocompute_metal_anion_binding_energy` | `data/public/autocompute_metal_anion_binding_energy.csv` | rows | 498 |
| `autocompute_example_small_molecules` | `data/public/autocompute_example_small_molecules.csv` | rows | 4 |

The Autocompute rows correspond to the public small-molecule database exposed by
the CEMP web database pages and are committed as CSV files under `data/public/`.

Count definitions:

- `rows` means CSV data rows, excluding the header row.
- `data points` means non-empty measured property values. For
  `paper_polymer_experiment_polymer_data.csv`, this is 21,402 measured property
  values across 13,116 polymer records.
- Quantum chemistry and other theoretical calculation CSV files are counted as
  `rows`.
- ML-generated prediction files are counted as `rows`.

More detailed data notes are available in `docs/data.md`.

## Local Release Commands

```bash
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
python manage.py verify_public_release --manifest data/public_manifest.json
```

`load_public_data` imports bundled demo CSV assets into SQLite. `seed_public_demo`
creates a local demo user and token. `verify_public_release` checks local demo
files, SHA256 values, count metadata, and release wording.

For a more complete local database, replace `--mode demo` with `--mode paper`.
Large file-based assets without a Django loader, such as the OMG polymer
prediction CSV, stay in `data/public/` and can be used directly with pandas,
spreadsheet software, or external analysis scripts.

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

## Further Documentation

| Document | Contents |
| --- | --- |
| `docs/install.md` | Local installation notes outside Docker. |
| `docs/deploy.md` | Docker deployment, CentOS notes, host ports, and health checks. |
| `docs/data.md` | Dataset descriptions, public CSV inventory, and source attribution notes. |
| `docs/api.md` | API usage examples with the local demo server. |
| `docs/reproduce.md` | Reproducibility workflow using the public assets. |
| `docs/availability_statement.md` | Data and code availability wording for manuscript or response use. |

## Citation

## Licenses

- Source code: Apache-2.0, see `LICENSE`.
- Public data and data/model assets: CC BY 4.0, see `DATA_LICENSE` and
  `data/public_manifest.json`.
