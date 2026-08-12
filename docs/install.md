# Installation

## Docker

```bash
git clone https://github.com/WangGroupFDU/CEMP_source_code.git
cd CEMP_source_code
cp .env.example .env
docker compose up --build
```

The container runs:

```bash
python manage.py migrate --noinput
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
python manage.py runserver 0.0.0.0:8000
```

Open `http://localhost:8000`.

For a shared server, set `CEMP_HOST_PORT` and host/CSRF values in `.env` before
starting Docker. See `docs/deploy.md` for CentOS, firewall, registry, and
port-selection notes. If Docker cannot create a bridge network on CentOS, use:

```bash
docker compose -f docker-compose.host-network.yml up -d --build
```

## Conda

Use the Anaconda base installation or Mamba-compatible Conda installation:

```bash
mamba env create -f environment.yml
conda activate cemp-public
python manage.py migrate
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
python manage.py runserver
```

## Configuration

Copy `.env.example` only when you need to customize settings. The public demo
uses SQLite by default.

Important variables:

| Variable | Purpose |
| --- | --- |
| `CEMP_SECRET_KEY` | Django secret key for a deployment. |
| `CEMP_HOST_PORT` | Host port published by Docker Compose. |
| `CEMP_CONTAINER_PORT` | Container listen port; default `8000`. |
| `CEMP_BASE_IMAGE` | Container base image or site-local mirror. |
| `CEMP_BUILD_NETWORK` | Docker build network mode; use `host` on Linux hosts with container DNS issues. |
| `CEMP_DEMO_FERNET_SEED` | Local seed used to derive the demo Fernet key. |
| `CEMP_FERNET_KEY` | Explicit Fernet key for persistent deployments. |
| `CEMP_SQLITE_PATH` | SQLite database path. |
| `CEMP_IL_MODEL_DIR` | Directory containing extracted ionic-liquid model assets. |
| `CEMP_POLYMER_MODEL_DIR` | Directory containing extracted polymer model assets. |
| `MP_API_KEY` | Optional Materials Project key for data refresh scripts. |

Scientific workflow variables:

| Variable | Purpose |
| --- | --- |
| `CEMP_SETTINGS_FILE` | Optional INI configuration file; environment variables override it. |
| `CEMP_GAUSSIAN16_BIN` | Gaussian 16 executable. |
| `CEMP_GAUSSIAN16_FORMCHK` | Gaussian `formchk` executable. |
| `CEMP_GAUSSIAN_DATABASE_PATH` | Writable Gaussian workflow cache/database directory. |
| `CEMP_GAUSSIAN_SCRATCH_DIR` | Writable Gaussian scratch directory used by the cleanup helper. |
| `CEMP_ORCA_PATH` | ORCA executable. |
| `CEMP_ORCA_2MKL_PATH` | ORCA `orca_2mkl` executable. |
| `CEMP_ORCA_DATABASE_PATH` | Writable ORCA workflow cache/database directory. |
| `CEMP_GMX_BIN` | GROMACS executable (`gmx` or `gmx_mpi`). |
| `CEMP_MULTIWFFN_EXE` | Multiwfn executable. |
| `CEMP_SOBTOP_HOME` | Sobtop installation directory. |
| `CEMP_OPENMPI_BIN` | Open MPI executable directory. |
| `CEMP_OPENMPI_LIB` | Open MPI library directory. |
| `CEMP_VMD_BIN` | VMD executable. |
| `CEMP_WORKFLOW_STATE_DIR` | Writable directory for workflow state, caches, and timing records. |

## Runtime Notes

- The demo path is CPU-only.
- The bundled demo database is generated locally by migrations and CSV imports.
- External scientific software is not bundled. Official project links, uses,
  and license notes are listed in the README. Gaussian 16 requires a separately
  obtained valid license.
- Model prediction APIs require `cemp_public_model_assets.tar.gz`; extract it
  and set `CEMP_IL_MODEL_DIR` or `CEMP_POLYMER_MODEL_DIR` when model files are
  outside their default directories.
- The complete active notebook inventory and execution order are documented in
  `docs/algorithms.md`.
