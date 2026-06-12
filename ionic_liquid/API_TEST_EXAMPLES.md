# Ionic Liquid API Examples

These examples use the local public demo workflow.

## Prepare Demo Data

```bash
python manage.py migrate
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
python manage.py runserver
```

Get a token:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/token/ \
  -d "username=cemp_demo" \
  -d "password=cemp_demo_local" | python -c 'import json,sys; print(json.load(sys.stdin)["token"])')
```

## Similarity Search

Endpoint:

```text
POST /ionic_liquid/api/similarity_search/
```

Example:

```bash
curl -X POST http://localhost:8000/ionic_liquid/api/similarity_search/ \
  -H "Authorization: Token ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "smiles": "CCO",
    "mol_type": "il",
    "source": "experiment",
    "topk": 3,
    "method": "tanimoto"
  }'
```

Expected response shape:

```json
{
  "results": [
    {
      "SMILES": "CC(=O)[O-].CC[NH3+]",
      "similarity": "string percentage",
      "Name": "ethylammonium acetate",
      "CAS": "",
      "properties": {
        "ECW (V)": "numeric value",
        "Tm (K)": "numeric value",
        "Conductivity (mS/cm)": "numeric value"
      }
    }
  ],
  "status": "success",
  "query": {
    "smiles": "CCO",
    "mol_type": "il",
    "source": "experiment",
    "topk": 3,
    "method": "tanimoto"
  }
}
```

## Property Filter

Endpoint:

```text
POST /ionic_liquid/api/property_filter/
```

Example:

```bash
curl -X POST http://localhost:8000/ionic_liquid/api/property_filter/ \
  -H "Authorization: Token ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "ecw_range": [3.0, 5.0],
    "conductivity_range": [0.1, 2.0],
    "tm_range": [300, 500],
    "source": "generated"
  }'
```

Expected response shape:

```json
{
  "results": [
    {
      "Name": "ethylammonium acetate",
      "SMILES": "CC(=O)[O-].CC[NH3+]",
      "properties": {
        "ECW (V)": 4.12,
        "Conductivity (mS/cm)": 1.34,
        "Tm (K)": 360.1
      }
    }
  ],
  "count": 1,
  "status": "success"
}
```

## Notes

- Use the demo token for protected endpoints.
- The bundled demo data is intentionally small, so result counts differ from the
  full paper data snapshot.
- Full paper data and model artifacts are listed in `data/public_manifest.json`.
