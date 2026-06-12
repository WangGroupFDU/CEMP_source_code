# Demo Login

The public release uses an explicit local demo user instead of hidden auto-login
behavior:

```bash
python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local
```

Use `http://localhost:8000/api/token/` to obtain a token for API examples.
