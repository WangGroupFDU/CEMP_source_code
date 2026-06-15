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
port-selection notes.

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
| `CEMP_BASE_IMAGE` | Container base image or site-local mirror. |
| `CEMP_BUILD_NETWORK` | Docker build network mode; use `host` on Linux hosts with container DNS issues. |
| `CEMP_DEMO_FERNET_SEED` | Local seed used to derive the demo Fernet key. |
| `CEMP_FERNET_KEY` | Explicit Fernet key for persistent deployments. |
| `CEMP_SQLITE_PATH` | SQLite database path. |
| `CEMP_IL_MODEL_DIR` | Directory containing extracted ionic-liquid model assets. |
| `MP_API_KEY` | Optional Materials Project key for data refresh scripts. |

## Runtime Notes

- The demo path is CPU-only.
- The bundled demo database is generated locally by migrations and CSV imports.
- Optional ORCA, Gaussian, GROMACS, and Multiwfn workflows require separate
  installation and license compliance.
- Model prediction APIs require `cemp_public_model_assets.tar.gz`; extract it
  and set `CEMP_IL_MODEL_DIR` when the model files are outside
  `ionic_liquid/static/model`.
- Full paper assets are archived outside the source tree and are listed in
  `data/public_manifest.json`.
