# API Notes

## Authentication

The public demo uses Django REST Framework token authentication for protected
API endpoints.

Create the demo user:

```bash
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
```

Request a token:

```bash
curl -X POST http://localhost:8000/api/token/ \
  -d "username=cemp_demo" \
  -d "password=cemp_demo_local"
```

Use the token:

```bash
curl http://localhost:8000/health/ \
  -H "Authorization: Token <TOKEN>"
```

## Demo Database Workflow

```bash
python manage.py migrate
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
```

The local demo data contains ionic-liquid, polymer, and battery rows for smoke
testing the database-backed views and APIs.

## Ionic Liquid Query Examples

Similarity and property-filter APIs are documented in
`ionic_liquid/API_TEST_EXAMPLES.md`. The examples use `http://localhost:8000`
and the demo token flow.

## Error Handling

Endpoints generally return JSON responses:

| Status | Meaning |
| --- | --- |
| `200` | Success. |
| `400` | Invalid request payload or missing parameter. |
| `401` | Authentication required or invalid token. |
| `404` | Requested data or file was not found. |
| `405` | Wrong HTTP method. |
| `500` | Unexpected server-side error. |

## External Compute APIs

AutoCompute endpoints can orchestrate optional scientific software workflows.
They are not required for the public demo workflow. Deployments that enable
these endpoints must provide their own compute nodes, software licenses, and
environment-specific configuration.
