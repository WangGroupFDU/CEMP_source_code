# CEMP Public Release Audit Report

## Scope

This report records the checks expected before publishing the open CEMP
manuscript-associated release. The release target is a reusable source package
with local demo data, public data/model manifests, and GitHub-hosted
paper-supporting assets.

## Current Release Policy

- Software license: Apache-2.0.
- Public data and model assets: CC BY 4.0 unless an asset-level manifest entry
  states otherwise.
- Local demo: SQLite plus bundled CSV files in `data/demo/`.
- Full paper database assets: CSV files committed under `data/public/`, with
  SHA256 values and count metadata recorded in `data/public_manifest.json`.
- Full paper model assets: GitHub Release attachments when the files are not
  suitable as regular repository files.

## Safety Checks

Before publishing a release, run:

```bash
python -m compileall -q .
python manage.py check
python manage.py test
python manage.py verify_public_release --manifest data/public_manifest.json
```

Also run a repository-wide credential scan for Django insecure key prefixes,
secret/key/password/token labels, private hosts, private IP ranges, user-local
absolute paths, private database dumps, Fernet-like tokens, cloud provider keys,
Google Maps browser keys, and Materials Project constructor calls with literal
tokens. Any real credential, private host, user data, log, uploaded file, task
result, or private database dump found by those checks must be removed before
publishing.

## Known Follow-Up Before Final Release

- Replace release-specific `TBD` commit/tag/checksum entries for full paper
  assets before final publication.
- Confirm source permissions for each public data/model asset before assigning
  CC BY 4.0.
- Rotate the Materials Project key that appeared in earlier local source copies;
  the current script reads `MP_API_KEY` from the environment.
