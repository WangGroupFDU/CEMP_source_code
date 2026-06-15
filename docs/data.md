# Public Data and Model Assets

## License

Public CEMP data, model metadata, and public data/model assets are released
under CC BY 4.0 unless an asset-level manifest entry states otherwise.

## Bundled Demo Assets

The repository includes small CSV files in `data/demo/` so that a third party
can run migrations, load data, seed a demo account, and exercise the main data
query path without private files.

Check them with:

```bash
python manage.py verify_public_release --manifest data/public_manifest.json
```

## GitHub Public CSV Assets

The repository also includes public CSV assets in `data/public/`.
Experimental datasets are counted as measured property `data_points`. Quantum
chemistry and ML-generated datasets are counted as `rows`.

| Asset | Count type | Count |
| --- | --- | ---: |
| `paper_ionic_liquid_il.csv` | rows | 1,065 |
| `paper_ionic_liquid_il_ml_data.csv` | rows | 100,000 |
| `paper_ionic_liquid_cation_qc_data.csv` | rows | 3,774 |
| `paper_ionic_liquid_anion_qc_data.csv` | rows | 2,220 |
| `paper_polymer_experiment_polymer_data.csv` | data points | 21,402 |
| `paper_polymer_calculated_monomer_data.csv` | rows | 10,519 |
| `paper_polymer_calculated_polymer_data.csv` | rows | 1,000 |
| `paper_bms_experiment_result.csv` | data points | 39 |
| `autocompute_cation_qc.csv` | rows | 431 |
| `autocompute_anion_qc.csv` | rows | 63 |
| `autocompute_ionic_liquid_qc.csv` | rows | 1,065 |
| `autocompute_electrolyte_qc.csv` | rows | 1,397 |
| `autocompute_li_electrolyte_qc.csv` | rows | 4,197 |
| `autocompute_metal_anion_binding_energy.csv` | rows | 498 |
| `autocompute_example_small_molecules.csv` | rows | 4 |
| `polymer_predicted_omg_deepsa_cemp_property.csv` | rows | 213,581 |

## Paper Data and Model Assets

The manuscript-supporting public database tables are committed as CSV files in
`data/public/` and represented in `data/public_manifest.json` as paper assets:

- paper public database CSV files with SHA256 checksums and count metadata;
- Autocompute small-molecule database CSV files with source attribution;
- model weights and scalers used by public prediction examples, attached to the
  GitHub Release when not committed as regular files:
  `cemp_public_model_assets.tar.gz`, 11,545,465 bytes,
  SHA256 `2f502c0b71a6da151265482ec4461b25a969a9417343b7580bfad0f2f7a9d007`;
- data dictionary and source-attribution notes.

## Data Dictionary Policy

Each public table should document:

- field name;
- physical or chemical meaning;
- unit;
- source;
- quality-control step;
- missing-value policy.

The minimum baseline recorded for the paper snapshot is:

| Table | Count type | Count |
| --- | --- | ---: |
| `ionic_liquid_il` | rows | 1,065 |
| `ionic_liquid_il_ml_data` | rows | 100,000 |
| `ionic_liquid_cation_qc_data` | rows | 3,774 |
| `ionic_liquid_anion_qc_data` | rows | 2,220 |
| `polymer_experiment_polymer_data` | data points | 21,402 |
| `polymer_calculated_monomer_data` | rows | 10,519 |
| `polymer_calculated_polymer_data` | rows | 1,000 |
| `battery_manage_system_bms_experiment_result` | data points | 39 |

## Source Attribution

Materials Project derived data must cite Materials Project and respect its data
terms. API refresh requires `MP_API_KEY`; no key is stored in this repository.

Quantum-chemistry and molecular-dynamics derived records should list the
software name, version when available, theory level or force-field setup, and
whether the workflow is ORCA, Gaussian, GROMACS, or precomputed.
