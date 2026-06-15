# Availability of Data and Materials

Draft text for manuscript or response letter:

The source code of CEMP is available at
`https://github.com/WangGroupFDU/CEMP_source_code` under the Apache License 2.0
(`Apache-2.0`). The manuscript-associated source release is planned as
`v1.0.0-paper-open` at commit `TBD`.

The public datasets, model metadata, data dictionary, and public model/data
assets supporting the manuscript are released under the Creative Commons
Attribution 4.0 International License (`CC BY 4.0`) unless an asset-level
manifest entry states otherwise. Public database tables are provided as CSV
files in the GitHub repository, with SHA256 checksums and count metadata recorded
in `data/public_manifest.json`.

The repository provides a local demo workflow that can be deployed without
private credentials:

```bash
docker compose up --build
```

or

```bash
python manage.py migrate
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
python manage.py verify_public_release --manifest data/public_manifest.json
python manage.py runserver
```

Optional ORCA, Gaussian, GROMACS, and Multiwfn workflows require independent
installation and license compliance, but the core public demo and manuscript
data/model checks use public data, public model assets, and precomputed records.
