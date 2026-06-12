# Battery Data Module

The public demo includes a small battery experiment metadata table in
`data/demo/bms_experiment_result.csv`. It is loaded with:

```bash
python manage.py load_public_data --manifest data/public_manifest.json --mode demo
```

The full paper-supporting battery table is listed in
`data/public_manifest.json` and should be archived with the complete public data
package before manuscript resubmission.
