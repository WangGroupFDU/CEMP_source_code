FROM condaforge/mambaforge:23.11.0-0

WORKDIR /app

COPY environment.yml /app/environment.yml
RUN mamba env update -n base -f /app/environment.yml && mamba clean -afy

COPY . /app

ENV CEMP_DEBUG=true \
    CEMP_SQLITE_PATH=/app/public_demo.sqlite3 \
    CEMP_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0 \
    CEMP_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000 \
    CEMP_SITE_DOMAIN=http://localhost:8000

EXPOSE 8000

CMD ["bash", "-lc", "python manage.py migrate --noinput && python manage.py load_public_data --manifest data/public_manifest.json --mode demo && python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local && python manage.py runserver 0.0.0.0:8000"]
