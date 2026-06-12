# Security and Publication Notes

## Configuration

CEMP public release settings are environment-driven. Important secrets and
deployment-specific values are read from environment variables such as
`CEMP_SECRET_KEY`, `CEMP_FERNET_KEY`, `CEMP_SQLITE_PATH`, and `MP_API_KEY`.

The local demo derives a Fernet key from `CEMP_DEMO_FERNET_SEED` if an explicit
`CEMP_FERNET_KEY` is not provided. This keeps the demo runnable while making it
clear that persistent deployments must provide their own key.

## Materials Project Key Handling

The crystal data refresh script requires `MP_API_KEY`. No Materials Project API
key should appear in source files, notebooks, documentation, commit messages, or
release notes. If a key was ever committed or shared, revoke it in Materials
Project and generate a replacement.

## Excluded Runtime State

Do not publish:

- real user accounts or tokens;
- sessions, admin logs, ticket contents, or email records;
- uploaded files, task outputs, scheduler logs, media folders, or private job
  directories;
- private compute-node inventory, SSH hosts, or server paths;
- private database backups or raw operational SQLite/MySQL dumps;
- unreviewed model artifacts whose training data or license is unclear.

## Release Gate

Run the checks documented in `PUBLICATION_AUDIT_REPORT.md` before every public
tag, GitHub Release, or Zenodo deposit.
