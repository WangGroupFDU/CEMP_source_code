# CEMP Public Code Snapshot

CEMP, the Clean Energy Materials Platform, is a Django-based research web platform for organizing materials data, querying molecular and materials records, running machine-learning prediction workflows, and orchestrating computational chemistry and molecular dynamics workflows used in clean-energy materials research.

This repository is a **sanitized public code snapshot** prepared for paper-related code release. It is intended to document the architecture, data flow, and implementation patterns of CEMP. It is **not** the complete production system and is **not expected to run as a deployed service without additional private data, configuration, credentials, databases, trained models, and scientific software environments**.

## What This Public Snapshot Is

This public snapshot provides source code examples for the main CEMP platform components:

- Django project configuration and URL routing.
- User registration, authentication, permission flags, and token-authenticated API access.
- Data-query interfaces for ionic liquids, polymers, crystals, and battery-management records.
- AutoCompute interfaces for high-throughput quantum chemistry, ORCA/Gaussian workflow templates, molecular dynamics workflow notebooks, and result-query pages.
- Selected workflow notebooks with execution outputs removed and comments stripped for public release.
- Sanitized templates, API views, model declarations, tests, and helper scripts.
- Security and publication notes describing how sensitive production data was removed.

The snapshot is designed for readers who want to understand **how CEMP is structured and how its computational workflows are represented in code**, rather than for users who want a plug-and-play deployment package.

## What This Public Snapshot Is Not

This public snapshot is intentionally incomplete. The following production assets are not included:

- Production databases and all user records.
- Uploaded files, task directories, logs, scheduler state, and generated results.
- Real deployment settings, secret keys, Fernet keys, SMTP credentials, SSH hosts, internal IP addresses, and absolute server paths.
- Private remote-computing node configuration.
- Large binary scientific software packages.
- Some trained model binaries and runtime datasets that were either private, too large, or not suitable for public redistribution.
- Production front-end build backups, cache directories, and historical debugging artifacts.

Placeholders such as `<CHANGE_ME_DJANGO_SECRET_KEY>`, `<CHANGE_ME_PASSWORD>`, `<PRIVATE_IP>`, `<PRIVATE_HOST>`, and `example.com` indicate values that existed in the private deployment but were removed for publication.

## Platform Overview

CEMP is organized as a multi-app Django project. The platform combines database-driven material browsing, machine-learning prediction, and automated calculation workflows under a single web interface.

At a high level, the system contains four layers:

1. **Web and account layer**: user registration, login, permissions, task-query pages, and ticketing.
2. **Materials database layer**: curated database tables and views for ionic liquids, polymers, crystals, and battery-related records.
3. **Prediction and search layer**: model-backed or descriptor-backed prediction utilities, structure visualization, and molecular similarity search.
4. **AutoCompute layer**: high-throughput quantum chemistry, ORCA/Gaussian workflow templates, MD workflow notebooks, remote scheduling helpers, and result-processing logic.

The production platform also used a remote execution environment for computationally expensive tasks. In this public snapshot, node-specific credentials and private deployment details have been removed.

## Repository Structure

| Path | Purpose |
| --- | --- |
| `cemp/` | Django project settings, root URL configuration, ASGI/WSGI entry points, and test settings. |
| `register/` | User registration, login, activation, permissions, API token handling, and profile models. |
| `home/` | Landing pages, task query pages, admin query templates, sitemap utilities, and shared website views. |
| `autocompute/` | Automated computation workflows, task models, API endpoints, notebook templates, remote execution utilities, molecular lookup helpers, and result-processing views. |
| `ionic_liquid/` | Ionic-liquid database models, data display pages, prediction helpers, and related templates. |
| `polymer/` | Polymer database models, polymer generation workflows, polymer property prediction utilities, and polymer visualization templates. |
| `crystals/` | Crystal/material database models, crystal structure utilities, prediction-related models, and crystal-property views. |
| `battery_manage_system/` | Battery experimental-data models, prediction-related views, and battery data visualization templates. |
| `tickets/` | User support ticket models, message models, and ticket views. |
| `contributor/` | Contributor and acknowledgement pages. |
| `tools/` | Public-release helper placeholder and release-workflow notes. |
| `PUBLICATION_AUDIT_REPORT.md` | Audit report for the sanitization and validation steps used to create this snapshot. |
| `SECURITY_PUBLICATION_NOTES.md` | Security notes explaining what was removed and why. |

## Core Modules

### User and Permission System

The `register` app defines user-facing account functionality and a `UserProfile` model with permission flags. In the production platform, these permission flags controlled access to database features, machine-learning features, AutoCompute tasks, and Gaussian-related workflows.

### Home and Task Query Pages

The `home` app contains shared pages and task-query interfaces. In production, users could inspect submitted tasks and administrators could inspect platform-level task history. Runtime task records and user-specific query results are not included.

### AutoCompute

The `autocompute` app is the main workflow layer for computational tasks. It contains models for computation tasks, upload/validation endpoints, result-query logic, remote execution utilities, and notebook-based workflow templates. The included areas cover quantum chemistry, ORCA/Gaussian workflows, MD preparation and post-analysis, ESP/HOMO-LUMO/NCI visualization, molecular lookup, and sanitized queue helpers.

### Ionic Liquid Database and Prediction

The `ionic_liquid` app contains ionic-liquid-related data models and views, including models for cations, anions, ionic-liquid records, lithium-electrolyte records, electrolyte records, and selected quantum-chemistry-derived datasets. Production database contents are not included.

### Polymer Database, Generation, and Prediction

The `polymer` app contains polymer-related database models, polymer generation workflow notebooks, polymer property prediction utilities, and structure visualization templates. Large generated files, private model artifacts, and production data exports were removed.

### Crystal and Materials Records

The `crystals` app contains crystal/material models, crystal structure utilities, prediction-related source files, templates, and static source files required to understand the module. Private database contents and runtime outputs are not included.

### Battery Management System

The `battery_manage_system` app contains battery experimental data models and associated prediction or visualization pages. Private experimental files, serialized data tables, and large binary model/runtime artifacts were removed.

### Ticketing and Contributor Pages

The `tickets` app provides a lightweight user-support workflow with ticket and ticket-message models. The `contributor` app provides contributor-facing pages. No private ticket content or user data is included.

## Computational Workflow Representation

CEMP uses notebook-centered workflow templates for many scientific procedures. These notebooks serve as executable protocol documents in the production environment. In this public release, notebooks are included to make the computational protocols inspectable, but outputs, execution counters, private paths, runtime data, and explanatory comments were removed.

## Security and Privacy Sanitization

This snapshot was prepared by copying a selected subset of the private repository into `CEMP_public` and applying publication sanitization. The process removed or replaced Django secret keys, Fernet keys, SMTP credentials, database passwords, API tokens, SSH users and hosts, internal and public deployment IP addresses, absolute server paths, production domain names, user emails, encrypted task identifiers, logs, databases, media folders, and task outputs.

See `SECURITY_PUBLICATION_NOTES.md` and `PUBLICATION_AUDIT_REPORT.md` for the detailed audit summary.

## Installation Notes for Code Inspection

This snapshot can be inspected with a standard Python environment. A minimal source-level check can be performed with:

```bash
python -m compileall -q CEMP_public
```

This command only checks Python syntax. It does not validate database connections, scientific workflows, front-end assets, queue workers, or notebook execution.

## Reproducibility Scope

This public code snapshot supports reproducibility at the level of software architecture, data-model design, workflow organization, view/API structure, computational protocol templates, and sanitized notebook logic. It does not support direct reproduction of the private production instance because production databases, user files, remote cluster configuration, and proprietary runtime environment are not included.

## Citation

If you use this code snapshot in academic work, cite the associated CEMP manuscript. Replace the placeholder below with the final citation after publication:

```text
CEMP: Clean Energy Materials Platform for Materials Data, Machine-Learning Prediction,
and Automated Computational Workflows. Manuscript in preparation / under review.
```

## License

No production license is implied by this sanitized snapshot. Before redistributing or reusing this code beyond paper review and inspection, add an explicit license file approved by the project owners.
