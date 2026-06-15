# Release Checklist

1. Run local checks:

```bash
python -m compileall -q .
python manage.py check
python manage.py test
python manage.py verify_public_release --manifest data/public_manifest.json
```

2. Generate public CSV data assets from the private SQLite source. If using a
   sanitized intermediate SQLite file, keep it local and publish the exported
   CSV files in `data/public/`:

```bash
python tools/export_public_csv_assets.py \
  --sqlite-path /path/to/private/db.sqlite3 \
  --paper-sqlite-path /path/to/sanitized_public_intermediate.sqlite3 \
  --polymer-prediction-csv /path/to/predicted_OMG_polymers_filter_DeepSA_CEMP_property.csv \
  --output-dir data/public
```

3. Package model weights, scalers, data dictionaries, and checksum files into
   `release_assets/`.

4. Create a GitHub Release for `v1.0.0-paper-open` and attach model archives
   that are not committed as regular repository files.

5. Replace release-specific `TBD` values in:

```text
README.md
data/public_manifest.json
docs/data.md
docs/availability_statement.md
GitHub Release notes
```

6. Confirm the Materials Project API key that appeared in earlier source copies
   has been revoked or rotated.
