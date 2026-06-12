# Release Checklist

1. Run local checks:

```bash
python -m compileall -q .
python manage.py check
python manage.py test
python manage.py verify_public_release --manifest data/public_manifest.json
```

2. Generate full public data asset from the private SQLite source:

```bash
python tools/create_public_sqlite_snapshot.py \
  --source /path/to/private/db.sqlite3 \
  --output release_assets/cemp_public_data.sqlite3 \
  --metadata release_assets/cemp_public_data.metadata.json
```

3. Package model weights, scalers, data dictionaries, and checksum files into
   `release_assets/`.

4. Upload release assets to Zenodo and create a GitHub Release for
   `v1.0.0-paper-open`.

5. Replace all `TBD` values in:

```text
README.md
data/public_manifest.json
docs/data.md
docs/availability_statement.md
GitHub Release notes
```

6. Confirm the Materials Project API key that appeared in earlier source copies
   has been revoked or rotated.
