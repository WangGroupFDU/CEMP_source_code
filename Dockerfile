ARG CEMP_BASE_IMAGE=quay.io/condaforge/miniforge3:23.11.0-0
FROM ${CEMP_BASE_IMAGE}

WORKDIR /app

COPY environment.yml /app/environment.yml
RUN if command -v mamba >/dev/null 2>&1; then \
      mamba env update -n base -f /app/environment.yml && mamba clean -afy; \
    else \
      conda env update -n base -f /app/environment.yml && conda clean -afy; \
    fi

COPY . /app

ENV CEMP_DEBUG=true \
    CEMP_SQLITE_PATH=/app/public_demo.sqlite3 \
    CEMP_CONTAINER_PORT=8000 \
    CEMP_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0 \
    CEMP_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000 \
    CEMP_SITE_DOMAIN=http://localhost:8000

EXPOSE 8000

CMD ["bash", "-lc", "python manage.py migrate --noinput && python manage.py load_public_data --manifest data/public_manifest.json --mode demo && python manage.py seed_public_demo --username cemp_demo --password cemp_demo_local && python manage.py runserver 0.0.0.0:${CEMP_CONTAINER_PORT:-8000}"]
