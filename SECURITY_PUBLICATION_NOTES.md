# Security and Publication Notes

This public snapshot was generated from a private research/deployment repository using whitelist copying, secret redaction, notebook output stripping, and comment removal.

## Sanitization Policy

- Real secrets and deployment endpoints were replaced with placeholders.
- Runtime databases, logs, media folders, task downloads, recovery SQL files, and generated outputs were excluded.
- Notebook outputs and execution counts were removed.
- Notebook explanatory comments and code comments were removed for public release.

## Before Public Release

Review `PUBLICATION_AUDIT_REPORT.md` and manually inspect any files listed under residual findings. Do not publish this snapshot if high-risk sensitive strings remain.
