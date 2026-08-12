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

The image and model-backed API path were validated on CentOS 8 using port
`8001` because port `8000` was occupied on the shared test host. The port is
configurable; see `docs/deploy.md` for the tested login, data-query, prediction,
export, and troubleshooting commands.

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
| `autocompute/static/` | Maintained MD, QC, analysis, and query notebook source used by task executors. |
| `polymer/static/programe/` | Maintained polymer generation and polymer inference notebooks. |
| `autocompute/public_algorithm_inventory.py` | Machine-readable allowlist for all 118 workflow and 5 inference notebooks. |
| `data/demo/` | Small local demo CSV assets for smoke tests and API examples. |
| `data/public/` | Public GitHub CSV assets, including Autocompute small molecules and polymer ML predictions. |
| `data/public_manifest.json` | Versioned data/model manifest, checksums, licenses, and release pointers. |
| `release_assets/` | Public model archive used by prediction examples and GitHub Release assets. |
| `.github/workflows/release.yml` | Tag-triggered GitHub Release workflow. |
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

| Data type | GitHub CSV location | Default local import | Notes |
| --- | --- | --- | --- |
| Small molecules | `data/public/autocompute_cation_qc.csv`, `data/public/autocompute_anion_qc.csv`, `data/public/autocompute_electrolyte_qc.csv`, `data/public/autocompute_li_electrolyte_qc.csv`, `data/public/autocompute_metal_anion_binding_energy.csv`, `data/public/autocompute_example_small_molecules.csv` | No, use `--mode paper` for the paper-linked subset | Public small-molecule database exports corresponding to `/autocompute/Database`. |
| Ionic liquids | `data/demo/ionic_liquid_*.csv`, `data/public/paper_ionic_liquid_il.csv`, `data/public/paper_ionic_liquid_il_ml_data.csv`, `data/public/paper_ionic_liquid_cation_qc_data.csv`, `data/public/paper_ionic_liquid_anion_qc_data.csv`, `data/public/autocompute_ionic_liquid_qc.csv` | Demo files with `--mode demo`; paper files with `--mode paper` | Includes ionic-liquid structures, ML rows, cation QC rows, anion QC rows, and the Autocompute ionic-liquid web-database copy. |
| Polymers | `data/demo/polymer_*.csv`, `data/public/paper_polymer_experiment_polymer_data.csv`, `data/public/paper_polymer_calculated_monomer_data.csv`, `data/public/paper_polymer_calculated_polymer_data.csv`, `data/public/polymer_predicted_omg_deepsa_cemp_property.csv` | Demo files with `--mode demo`; paper-linked CSV files with `--mode paper`; prediction CSV stays file-based | Includes experimental polymer properties, calculated monomer/polymer properties, and 213,581 OMG polymer ML prediction rows. |
| Crystals | `data/public/crystal_al_cleaned.csv`, `data/public/crystal_ba_cleaned.csv`, `data/public/crystal_ca_cleaned.csv`, `data/public/crystal_k_cleaned.csv`, `data/public/crystal_li_cleaned.csv`, `data/public/crystal_mg_cleaned.csv`, `data/public/crystal_na_cleaned.csv`, `data/public/crystal_zn_cleaned.csv` | Paper files with `--mode paper` | Materials Project-derived crystal database snapshots for Al, Ba, Ca, K, Li, Mg, Na, and Zn-containing materials. Crystal prediction model weights are public in `release_assets/cemp_public_model_assets.tar.gz`; optional Materials Project refresh scripts require a user-provided `MP_API_KEY`. |
| Battery data | `data/demo/bms_experiment_result.csv`, `data/public/paper_bms_experiment_result.csv` | Demo file with `--mode demo`; paper file with `--mode paper` | Public battery experiment records used for database browsing and release checks. |
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

The repository includes demo CSV files, public database CSV assets, and the
public model archive directly. The tagged GitHub Release also attaches the
model archive for convenient download. The manifest records the expected public
snapshot baseline.
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
| `paper_crystal_al_cleaned` | `data/public/crystal_al_cleaned.csv` | rows | 7,797 |
| `paper_crystal_ba_cleaned` | `data/public/crystal_ba_cleaned.csv` | rows | 8,334 |
| `paper_crystal_ca_cleaned` | `data/public/crystal_ca_cleaned.csv` | rows | 8,421 |
| `paper_crystal_k_cleaned` | `data/public/crystal_k_cleaned.csv` | rows | 8,034 |
| `paper_crystal_li_cleaned` | `data/public/crystal_li_cleaned.csv` | rows | 21,574 |
| `paper_crystal_mg_cleaned` | `data/public/crystal_mg_cleaned.csv` | rows | 19,007 |
| `paper_crystal_na_cleaned` | `data/public/crystal_na_cleaned.csv` | rows | 12,792 |
| `paper_crystal_zn_cleaned` | `data/public/crystal_zn_cleaned.csv` | rows | 6,905 |
| `autocompute_cation_qc` | `data/public/autocompute_cation_qc.csv` | rows | 431 |
| `autocompute_anion_qc` | `data/public/autocompute_anion_qc.csv` | rows | 63 |
| `autocompute_ionic_liquid_qc` | `data/public/autocompute_ionic_liquid_qc.csv` | rows | 1,065 |
| `autocompute_electrolyte_qc` | `data/public/autocompute_electrolyte_qc.csv` | rows | 1,397 |
| `autocompute_li_electrolyte_qc` | `data/public/autocompute_li_electrolyte_qc.csv` | rows | 4,197 |
| `autocompute_metal_anion_binding_energy` | `data/public/autocompute_metal_anion_binding_energy.csv` | rows | 498 |
| `autocompute_example_small_molecules` | `data/public/autocompute_example_small_molecules.csv` | rows | 4 |

The Autocompute rows correspond to the public small-molecule database exposed by
the CEMP web database pages and are committed as CSV files under `data/public/`.
The crystal CSV assets contain 92,864 Materials Project-derived rows in total.

Count definitions:

- `rows` means CSV data rows, excluding the header row.
- `data points` means non-empty measured property values. For
  `paper_polymer_experiment_polymer_data.csv`, this is 21,402 measured property
  values across 13,116 polymer records.
- Quantum chemistry and other theoretical calculation CSV files are counted as
  `rows`.
- ML-generated prediction files are counted as `rows`.

More detailed data notes are available in `docs/data.md`.

### Public Model Archive

All public model files required by the open prediction examples are packaged in:

```text
release_assets/cemp_public_model_assets.tar.gz
```

The archive is tracked in this repository and is also uploaded to the
[`v1.1.0-paper-open` GitHub Release](https://github.com/WangGroupFDU/CEMP_source_code/releases/tag/v1.1.0-paper-open).
It is licensed under CC BY 4.0 as recorded in `data/public_manifest.json`.

```text
size: 11,377,421 bytes
sha256: 8bf69f11a9c128cf788a84cc618577d8858dffc7ae8f39a40f12237adbc04062
```

Extract it at the repository root to restore the model files to the runtime
paths used by the Django views:

```bash
tar -xzf release_assets/cemp_public_model_assets.tar.gz -C .
```

The Docker image performs this extraction during image build.

| Model group | Files included in the archive |
| --- | --- |
| Ionic-liquid property models | `ionic_liquid/static/model/conductivity_xgb_model.joblib`, `Ea_xgb_model.joblib`, `lnA_xgb_model.joblib`, `ECW_xgb_model.joblib`, `Tm_xgb_model.joblib`, `IL_ECW_xgb_model.joblib`, `Tm_xgb_model_fp.joblib`, `IL_ECW_xgb_model_fp.joblib`, `conductivity_MLP_model_fp.pt`, `MLPModel.py`, `prediction_model.ipynb`, `IL_property_prediction_test.xlsx` |
| Polymer property models | `polymer/static/model/Youngs_Modulus_xgb_model.joblib`, `Tm_xgb_model.joblib`, `Tg_xgb_model.joblib`, `Tensile_Strength_xgb_model.joblib`, `Dielectric_Constant_Total_xgb_model.joblib` |
| Crystal prediction models | `crystals/static/prediction_model/average_voltage_MOCO+GAT.pth`, `capacity_grav_MOCO+GAT.pth`, `energy_grav_MOCO+GAT.pth`, `average_voltage_GCN.pth`, `capacity_grav_GCN.pth`, `energy_grav_GCN.pth`, `average_voltage_GAT.pth`, `capacity_grav_GAT.pth`, `energy_grav_GAT.pth` |

## Algorithm Source And Execution

The repository contains the source notebooks that are currently called by a
CEMP page, API, task executor, or maintained prediction example. The release
allowlist contains 123 notebooks:

| Algorithm group | Notebooks | Main source location |
| --- | ---: | --- |
| Standard molecular dynamics | 12 | `autocompute/static/MDAutocompute_programe/` |
| ORCA molecular dynamics | 8 | `autocompute/static/MDAutocompute_programe_ORCA/` |
| Gaussian quantum-chemistry workflows | 48 | `autocompute/static/QcAutocompute_programe/HTQC_*/` |
| ORCA quantum chemistry and manual mode | 26 | `autocompute/static/QcAutocompute_programe/ORCA_*/` |
| ESP, orbital, NCI, and SMILES-query workflows | 6 | `autocompute/static/drawESP/`, `draw_HOMO_LUMO_orb/`, `NCIanalysis/`, `NCI_analysis_promolecular/`, and `query_SMILES/` |
| Linear and cyclic polymer generation | 18 | `polymer/static/programe/generate_*/` |
| Model inference examples | 5 | `ionic_liquid/static/` and `polymer/static/programe/predict_*/` |

AutoCompute copies the selected workflow and
`autocompute/static/cemp_software_settings.py` into a task directory, then runs
the registered notebooks sequentially with `jupyter nbconvert --execute`.
Notebook order, task types, execution functions, helper modules, and external
dependencies are documented in `docs/algorithms.md` and defined in
`autocompute/public_algorithm_inventory.py`.

The ionic-liquid notebook at
`ionic_liquid/static/model/prediction_model.ipynb` is also maintained as an
independent CPU inference example. Extract the model archive first, then set
`CEMP_IL_MODEL_DIR` if the models are not under
`ionic_liquid/static/model/`. Polymer examples use `CEMP_POLYMER_MODEL_DIR` in
the same way.

### Scientific Software Configuration

Scientific software is configured through environment variables. Empty values
are acceptable for the Docker data/demo path; a workflow requires only the
variables for the software it calls.

| Variable | Value |
| --- | --- |
| `CEMP_GAUSSIAN16_BIN` | Gaussian 16 executable, such as `g16`. |
| `CEMP_GAUSSIAN16_FORMCHK` | Gaussian `formchk` executable. |
| `CEMP_GAUSSIAN_DATABASE_PATH` | Writable Gaussian calculation cache/database directory. |
| `CEMP_GAUSSIAN_SCRATCH_DIR` | Writable Gaussian scratch directory used by the cleanup helper. |
| `CEMP_ORCA_PATH` | ORCA executable. |
| `CEMP_ORCA_2MKL_PATH` | ORCA `orca_2mkl` executable. |
| `CEMP_ORCA_DATABASE_PATH` | Writable ORCA calculation cache/database directory. |
| `CEMP_GMX_BIN` | GROMACS executable, such as `gmx` or `gmx_mpi`. |
| `CEMP_MULTIWFFN_EXE` | Multiwfn executable. |
| `CEMP_SOBTOP_HOME` | Sobtop installation directory. |
| `CEMP_OPENMPI_BIN` | Open MPI executable directory. |
| `CEMP_OPENMPI_LIB` | Open MPI library directory. |
| `CEMP_VMD_BIN` | VMD executable. |
| `CEMP_WORKFLOW_STATE_DIR` | Writable directory for workflow caches and timing records. |

An optional INI file may be selected with `CEMP_SETTINGS_FILE`; environment
variables override values from the INI file.

## Local Release Commands

```bash
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
python manage.py verify_public_release --manifest data/public_manifest.json
```

`load_public_data` imports bundled demo CSV assets into SQLite. `seed_public_demo`
creates a local demo user and token. `verify_public_release` checks local demo
files, SHA256 values, count metadata, release wording, the 123-notebook
allowlist, notebook syntax and output state, helper modules, and shared workflow
configuration.

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

## External Scientific Software

External scientific programs are not distributed with CEMP. Install only the
programs required by the workflow being run and follow the upstream license and
registration terms.

| Software | Use in CEMP | Official download or project page | Distributed with CEMP | Requirement |
| --- | --- | --- | --- | --- |
| Gaussian 16 | Gaussian QC, RESP, and selected MD preparation stages | [Gaussian 16](https://gaussian.com/gaussian16/) | No | Proprietary software; a separately obtained valid license is required. |
| ORCA | ORCA QC and ORCA-MD quantum-chemistry stages | [ORCA](https://www.faccts.de/orca/) | No | Install and use under the current FACCTs/ORCA terms. |
| GROMACS | Molecular-dynamics preparation, simulation, and analysis | [GROMACS downloads](https://manual.gromacs.org/current/download.html) | No | Install and use under the upstream license. |
| Sobtop | Molecular topology generation and topology repair | [Sobtop](http://sobereva.com/soft/Sobtop/) | No | Follow the terms published by the author. |
| Multiwfn | Wavefunction, charge, ESP, orbital, and NCI analysis | [Multiwfn](http://sobereva.com/multiwfn/) | No | Follow the terms published by the author. |
| Open Babel | Molecular format conversion and structure handling | [Open Babel installation](https://openbabel.org/docs/Installation/install.html) | No | Install and use under the upstream license. |
| Open MPI | Parallel runtime used by configured ORCA/GROMACS installations | [Open MPI](https://www.open-mpi.org/software/ompi/) | No | Install and use under the upstream license. |
| VMD | Trajectory, orbital, ESP, and NCI visualization | [VMD](https://www.ks.uiuc.edu/Research/vmd/) | No | Registration or license acceptance may be required by the upstream distributor. |

These programs are optional for the public web demo. Database browsing, CSV
validation, demo login, and the bundled CPU model checks use the public data,
public model assets, and precomputed records.

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
| `docs/algorithms.md` | Active algorithm inventory, notebook order, task executors, and external dependencies. |
| `docs/availability_statement.md` | Data and code availability wording for manuscript or response use. |
| `docs/release_notes/v1.1.0-paper-open.md` | Changes and validation notes for the algorithm-source release. |

## Citation

## Licenses

- Source code: Apache-2.0, see `LICENSE`.
- Public data and data/model assets: CC BY 4.0, see `DATA_LICENSE` and
  `data/public_manifest.json`.
