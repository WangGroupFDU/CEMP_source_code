# Polymer Module Public Deployment Checklist

Use the top-level installation workflow:

```bash
python manage.py migrate
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
```

The bundled polymer demo records are in `data/demo/`. Full polymer data and
model assets should be archived through the release asset workflow described in
`docs/data.md`.
