# Public Data and Model Assets

## License

Public CEMP data, model metadata, and archived data/model assets are released
under CC BY 4.0 unless an asset-level manifest entry states otherwise.

## Bundled Demo Assets

The repository includes small CSV files in `data/demo/` so that a third party
can run migrations, load data, seed a demo account, and exercise the main data
query path without private files.

Check them with:

```bash
python manage.py verify_public_release --manifest data/public_manifest.json
```

## Full Paper Assets

The full manuscript-supporting public data and model package is represented in
`data/public_manifest.json` as paper assets. These assets are intended for
GitHub Release and Zenodo archival:

- public SQLite data snapshot: `cemp_public_data.sqlite3`, 32,903,168 bytes,
  SHA256 `307ace04834599f4e3d2adce3f092bd810e54e7e73686d3d63e8863712386bab`;
- CSV/XLSX exports for ionic liquid, polymer, crystal, and battery tables;
- model weights and scalers used by public prediction examples:
  `cemp_public_model_assets.tar.gz`, 11,545,465 bytes,
  SHA256 `2f502c0b71a6da151265482ec4461b25a969a9417343b7580bfad0f2f7a9d007`;
- SHA256 checksum file;
- data dictionary and source-attribution notes.

The DOI is `TBD` until the Zenodo deposit is completed. After archival, update:

```text
data/public_manifest.json
docs/availability_statement.md
README.md
GitHub Release notes
```

## Data Dictionary Policy

Each public table should document:

- field name;
- physical or chemical meaning;
- unit;
- source;
- quality-control step;
- missing-value policy.

The minimum table-row baseline recorded for the paper snapshot is:

| Table | Rows |
| --- | ---: |
| `ionic_liquid_il` | 1,065 |
| `ionic_liquid_il_ml_data` | 100,000 |
| `ionic_liquid_cation_qc_data` | 3,774 |
| `ionic_liquid_anion_qc_data` | 2,220 |
| `polymer_experiment_polymer_data` | 13,116 |
| `polymer_calculated_monomer_data` | 10,519 |
| `polymer_calculated_polymer_data` | 1,000 |
| `battery_manage_system_bms_experiment_result` | 39 |

## Source Attribution

Materials Project derived data must cite Materials Project and respect its data
terms. API refresh requires `MP_API_KEY`; no key is stored in this repository.

Quantum-chemistry and molecular-dynamics derived records should list the
software name, version when available, theory level or force-field setup, and
whether the workflow is ORCA, Gaussian, GROMACS, or precomputed.
