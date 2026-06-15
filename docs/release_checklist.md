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

3. Confirm the public model archive is committed and checksum-stable:

```bash
shasum -a 256 release_assets/cemp_public_model_assets.tar.gz
```

4. Tag the manuscript release. The `.github/workflows/release.yml` workflow
   creates or updates the GitHub Release and uploads
   `release_assets/cemp_public_model_assets.tar.gz`:

```bash
git tag -a v1.0.0-paper-open -m "CEMP v1.0.0-paper-open"
git push origin v1.0.0-paper-open
```

5. Confirm release-specific values in:

```text
README.md
data/public_manifest.json
docs/data.md
docs/availability_statement.md
docs/release_notes/v1.0.0-paper-open.md
```

6. Confirm the Materials Project API key that appeared in earlier source copies
   has been revoked or rotated.
