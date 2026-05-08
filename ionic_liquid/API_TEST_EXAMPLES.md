# Ionic Liquid Query API - Test Examples

## Overview
This document provides test examples for the two new API endpoints for ionic liquid query functionality.

**Note**: All example responses marked as "Real Response" are actual API responses from the production server (`https://example.com`), verified on 2025-10-17.

## API Endpoints

### 1. Similarity Search API
**URL**: `/ionic_liquid/api/similarity_search/`
**Method**: POST
**Content-Type**: application/json

#### Request Parameters
- `smiles` (string, required): Query SMILES string
- `mol_type` (string, required): Material type - "IL", "Cation", or "Anion"
- `source` (string, required): Data source - "experiment" or "generated"
- `topk` (integer, optional): Number of results to return (default: 10)
- `method` (string, optional): Similarity method - "tanimoto", "dice", "cosine", "tversky" (default: "tanimoto")

#### Example 1: Query Similar IL (Experimental) - Simple SMILES
```bash
curl -X POST https://example.com/ionic_liquid/api/similarity_search/ \
  -H "Content-Type: application/json" \
  -d '{
    "smiles": "CCO",
    "mol_type": "il",
    "source": "experiment",
    "topk": 3
  }'
```

**Real Response:**
```json
{
  "results": [
    {
      "SMILES": "CCC[N+](C)(C)CCO.[Br-]",
      "similarity": "27.78%",
      "Name": "N-(2-hydroxyethyl)-N,N-dimethylpropanaminium bromide",
      "CAS": "",
      "properties": {
        "ECW (V)": "1.918901085853577",
        "Tm (K)": "372.595",
        "Conductivity (mS/cm)": "1.001187801361084"
      }
    },
    {
      "SMILES": "CC(=O)[O-].CC[NH3+]",
      "similarity": "26.67%",
      "Name": "ethylammonium acetate",
      "CAS": "",
      "properties": {
        "ECW (V)": "0.1632136",
        "Tm (K)": "360.125",
        "Conductivity (mS/cm)": "1.336334228515625"
      }
    },
    {
      "SMILES": "C[N+](C)(C)CCO.[Br-]",
      "similarity": "26.67%",
      "Name": "choline bromide",
      "CAS": "",
      "properties": {
        "ECW (V)": "1.287918210029602",
        "Tm (K)": "472.875",
        "Conductivity (mS/cm)": "0.6049426794052124"
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

#### Example 2: Query Similar Anion (Generated)
```bash
curl -X POST http://localhost:8000/ionic_liquid/api/similarity_search/ \
  -H "Content-Type: application/json" \
  -d '{
    "smiles": "CCOS(=O)(=O)[O-]",
    "mol_type": "Anion",
    "source": "generated",
    "topk": 3
  }'
```

**Expected Response:**
```json
{
  "results": [
    {
      "SMILES": "CCOS(=O)(=O)[O-]",
      "similarity": "100.00%",
      "Name": "a-c17+a-b15",
      "CAS": "",
      "properties": {
        "HOMO (Hatree)": "-0.07903",
        "LUMO (Hatree)": "0.17326"
      }
    },
    {
      "SMILES": "CCCCOS(=O)(=O)[O-]",
      "similarity": "54.55%",
      "Name": "a-c17+a-b14",
      "CAS": "",
      "properties": {
        "HOMO (Hatree)": "-0.08662",
        "LUMO (Hatree)": "0.15771"
      }
    }
  ],
  "status": "success"
}
```

---

### 2. Property Filter API
**URL**: `/ionic_liquid/api/property_filter/`
**Method**: POST
**Content-Type**: application/json

#### Request Parameters
- `ecw_range` (array or null): [min, max] for ECW in Volts (e.g., `[4.0, 5.0]` or `[4.5, null]` or `null`)
- `conductivity_range` (array or null): [min, max] for Conductivity in mS/cm
- `tm_range` (array or null): [min, max] for Melting point in Kelvin
- `source` (string, required): "experiment" or "generated"

**Note**: Any range parameter can be:
- `null` - no constraint on that property
- `[min, null]` - only minimum constraint
- `[null, max]` - only maximum constraint
- `[min, max]` - both minimum and maximum constraints

#### Example 1: Filter by ECW, Conductivity and Melting Point
```bash
curl -X POST https://example.com/ionic_liquid/api/property_filter/ \
  -H "Content-Type: application/json" \
  -d '{
    "ecw_range": [4.5, 5],
    "conductivity_range": [1, 2],
    "tm_range": [300, 350],
    "source": "experiment"
  }'
```

**Real Response:**
```json
{
  "results": [
    {
      "Name": "1-butyronitrile-3-methylimidazolium tetrafluoroborate",
      "SMILES": "Cn1cc[n+](CCCC#N)c1.F[B-](F)(F)F",
      "CAS": "",
      "properties": {
        "ECW (V)": 4.909222602844238,
        "Conductivity (mS/cm)": 1.1901457,
        "Tm (K)": 308.7811279296875
      }
    },
    {
      "Name": "N-adamantyl-N,N-dimethyl-N-octylammonium bis(fluorosulfonyl)amide",
      "SMILES": "CCCCCCCC[N+](C)(C)C12CC3CC(CC(C3)C1)C2.O=S(=O)(F)[N-]S(=O)(=O)F",
      "CAS": "",
      "properties": {
        "ECW (V)": 4.66162304,
        "Conductivity (mS/cm)": 1.883614659309387,
        "Tm (K)": 349.4
      }
    },
    {
      "Name": "methyltripropylammonium bis[(trifluoromethyl)sulfonyl]amide",
      "SMILES": "CCC[N+](C)(CCC)CCC.O=S(=O)([N-]S(=O)(=O)C(F)(F)F)C(F)(F)F",
      "CAS": "",
      "properties": {
        "ECW (V)": 4.760197162628174,
        "Conductivity (mS/cm)": 1.652505159378052,
        "Tm (K)": 319.1
      }
    },
    {
      "Name": "1-(2-((3-fluoro-4-methylphenyl)amino)-2-oxoethyl)-4-methylpyridin-1-ium hexafluorophosphate",
      "SMILES": "Cc1cc[n+](CC(=O)Nc2ccc(C)c(F)c2)cc1.F[P-](F)(F)(F)(F)F",
      "CAS": "",
      "properties": {
        "ECW (V)": 4.73285984,
        "Conductivity (mS/cm)": 1.028069257736206,
        "Tm (K)": 339.6
      }
    }
  ],
  "count": 4,
  "status": "success",
  "filters": {
    "ecw_range": [4.5, 5],
    "conductivity_range": [1, 2],
    "tm_range": [300, 350],
    "source": "experiment"
  }
}
```

#### Example 2: Filter by All Three Properties
```bash
curl -X POST http://localhost:8000/ionic_liquid/api/property_filter/ \
  -H "Content-Type: application/json" \
  -d '{
    "ecw_range": [4.0, 5.0],
    "conductivity_range": [2, 25],
    "tm_range": [300, 400],
    "source": "generated"
  }'
```

**Expected Response:**
```json
{
  "results": [

  ],
  "count": 156,
  "status": "success",
  "filters": {
    "ecw_range": [4.0, 5.0],
    "conductivity_range": [2, 25],
    "tm_range": [300, 400],
    "source": "generated"
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "SMILES parameter is required"
}
```

### 404 Not Found
```json
{
  "error": "Database for il/experiment not found or empty"
}
```

### 500 Internal Server Error
```json
{
  "error": "Input SMILES cannot be parsed by RDKit",
  "traceback": "..."
}
```

---

## Python Test Script

```python
import requests
import json

BASE_URL = "http://localhost:8000/ionic_liquid"


def test_similarity_search():
    url = f"{BASE_URL}/api/similarity_search/"
    payload = {
        "smiles": "CCCCCCN1C=C[N+](=C1)C.C(=C(C
        "mol_type": "IL",
        "source": "experiment",
        "topk": 3,
        "method": "tanimoto"
    }
    response = requests.post(url, json=payload)
    print("Similarity Search Response:")
    print(json.dumps(response.json(), indent=2))
    return response.json()


def test_property_filter():
    url = f"{BASE_URL}/api/property_filter/"
    payload = {
        "ecw_range": [4.0, 5.0],
        "conductivity_range": None,
        "tm_range": [300, 350],
        "source": "generated"
    }
    response = requests.post(url, json=payload)
    print("Property Filter Response:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

if __name__ == "__main__":
    test_similarity_search()
    print("\n" + "="*50 + "\n")
    test_property_filter()
```

---

## Database File Requirements

The API requires 6 Morgan fingerprint database files in:
`ionic_liquid/test_box/query_similar_IL/`

Required files:
1. `experiment_IL_smiles_morgan_fp.json.gz`
2. `generated_IL_smiles_morgan_fp.json.gz`
3. `experiment_cation_smiles_morgan_fp.json.gz`
4. `generated_cation_smiles_morgan_fp.json.gz`
5. `experiment_anion_smiles_morgan_fp.json.gz`
6. `generated_anion_smiles_morgan_fp.json.gz`

These files are generated from the notebook: `2_query_similar_monomer_test.ipynb`

---

## Frontend Integration Notes

### Similarity Search Form
- Dropdown 1: mol_type ["IL", "Cation", "Anion"]
- Dropdown 2: source ["experiment", "generated"]
- Text input: SMILES string
- Number input: topk (default: 10)
- Submit button

### Property Filter Form
- Dropdown: source ["experiment", "generated"]
- Range slider/inputs: ECW (V) [min, max]
- Range slider/inputs: Conductivity (mS/cm) [min, max]
- Range slider/inputs: Melting point (K) [min, max]
- Submit button

### Results Display
- Use DataTable or similar to display results
- Show columns: SMILES, Name, CAS, Similarity%, Properties
- Enable sorting and filtering
- Export to CSV/Excel functionality
