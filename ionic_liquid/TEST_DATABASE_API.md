# Ionic Liquid Database API Test Notes

Load the local demo data before testing database-backed endpoints:

```bash
python manage.py migrate
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
```

Use `ionic_liquid/API_TEST_EXAMPLES.md` for request examples. All public examples
should use `http://localhost:8000` and the demo token flow.
