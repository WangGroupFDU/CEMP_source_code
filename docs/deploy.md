# Docker Deployment Notes

## Scope

This document describes the public CEMP Docker demo deployment path. It is
intended for a Linux host such as CentOS 8 with Docker Engine and Docker Compose
v2 already installed.

The Docker path starts a single Django container with SQLite demo data. It does
not require MySQL, private compute nodes, ORCA, Gaussian, GROMACS, Multiwfn, or
a Materials Project API key.

## Prerequisites

- Docker Engine is installed and the current user can run `docker`.
- Docker Compose v2 is available as `docker compose`.
- The host can reach a container registry for the base image.
- The host can reach conda-forge during the first image build.
- A host TCP port is available for the Django service.

Check the host:

```bash
docker --version
docker compose version
curl -I https://quay.io/v2/
curl -I https://conda.anaconda.org/conda-forge/
ss -ltn
```

The default base image is:

```text
quay.io/condaforge/miniforge3:23.11.0-0
```

This avoids depending on Docker Hub for the default public image build. If a
site-local mirror is required, set `CEMP_BASE_IMAGE` before building.

On Linux servers where Docker build containers cannot resolve external DNS while
the host itself can, keep:

```text
CEMP_BUILD_NETWORK=host
```

This setting affects the image build step only. The running service still uses
normal Compose networking and publishes only `CEMP_HOST_PORT`.

## Port Selection

The container listens on port `8000` internally. The host port is controlled by
`CEMP_HOST_PORT`.

For a local workstation:

```bash
CEMP_HOST_PORT=8000
```

For a shared server, choose a free port, for example:

```bash
ss -ltn | grep ':18080 ' || echo '18080 is free'
CEMP_HOST_PORT=18080
```

The public URL must match Django host and CSRF settings:

```bash
CEMP_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0,<server-ip-or-domain>
CEMP_CSRF_TRUSTED_ORIGINS=http://localhost:18080,http://127.0.0.1:18080,http://<server-ip-or-domain>:18080
CEMP_SITE_DOMAIN=http://<server-ip-or-domain>:18080
```

If firewalld is enabled and remote browser access is required, open the selected
host port:

```bash
sudo firewall-cmd --add-port=18080/tcp --permanent
sudo firewall-cmd --reload
```

## Deployment Steps

Clone the repository and create a local `.env` file:

```bash
git clone https://github.com/WangGroupFDU/CEMP_source_code.git
cd CEMP_source_code
cp .env.example .env
```

Edit `.env` for the target host. For a shared server using host port `18080`,
set at least:

```text
CEMP_HOST_PORT=18080
CEMP_BUILD_NETWORK=host
CEMP_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0,<server-ip-or-domain>
CEMP_CSRF_TRUSTED_ORIGINS=http://localhost:18080,http://127.0.0.1:18080,http://<server-ip-or-domain>:18080
CEMP_SITE_DOMAIN=http://<server-ip-or-domain>:18080
```

Build and start:

```bash
docker compose up -d --build
```

The first build creates a conda environment from `environment.yml`. This can
take several minutes and requires access to conda-forge.

## Validation

Check the generated Compose configuration:

```bash
docker compose config | sed -n '/ports:/,/volumes:/p'
```

Check service status and logs:

```bash
docker compose ps
docker compose logs --tail=120 cemp
```

Health checks:

```bash
curl -fsS http://127.0.0.1:${CEMP_HOST_PORT:-8000}/health/
curl -fsS http://127.0.0.1:${CEMP_HOST_PORT:-8000}/homepage_stats/
```

Expected local demo account:

```text
username: cemp_demo
password: cemp_demo_local
```

## Open Port

Only one host port is opened by the Compose deployment:

```text
<CEMP_HOST_PORT>/tcp -> container 8000/tcp
```

For example, with `CEMP_HOST_PORT=18080`:

```text
http://<server-ip-or-domain>:18080
```

No database port is published by the public demo Compose file.

## Common Failures

### Host Port Already In Use

Symptom:

```text
Bind for 0.0.0.0:8000 failed: port is already allocated
```

Fix:

```bash
CEMP_HOST_PORT=18080 docker compose up -d --build
```

or set `CEMP_HOST_PORT=18080` in `.env`.

### Registry Is Unreachable

Symptom:

```text
failed to fetch anonymous token
failed to resolve source metadata
```

Fixes:

- confirm `curl -I https://quay.io/v2/` works from the host;
- configure the Docker daemon proxy or registry mirror if required by the site;
- set `CEMP_BASE_IMAGE` to a site-local mirror of
  `quay.io/condaforge/miniforge3:23.11.0-0`.
- set `CEMP_BUILD_NETWORK=host` when the host can resolve package endpoints but
  Docker build containers cannot.

### Conda Packages Cannot Be Downloaded

Symptom:

```text
CondaHTTPError
PackagesNotFoundError
```

Fixes:

- confirm `curl -I https://conda.anaconda.org/conda-forge/` works;
- configure conda mirror/proxy according to the host network policy;
- rebuild with `docker compose build --no-cache` after fixing network access.

### DisallowedHost or CSRF Errors

Symptom:

```text
Invalid HTTP_HOST header
CSRF verification failed
```

Fix `.env`:

```text
CEMP_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0,<server-ip-or-domain>
CEMP_CSRF_TRUSTED_ORIGINS=http://localhost:<port>,http://127.0.0.1:<port>,http://<server-ip-or-domain>:<port>
CEMP_SITE_DOMAIN=http://<server-ip-or-domain>:<port>
```

Restart:

```bash
docker compose up -d
```

### Recreate the Demo Database

The demo SQLite database is inside the container filesystem. To recreate it:

```bash
docker compose down
docker compose up -d --build
```

For persistent custom deployments, set `CEMP_SQLITE_PATH` to a mounted path and
add an explicit volume in `docker-compose.yml`.
