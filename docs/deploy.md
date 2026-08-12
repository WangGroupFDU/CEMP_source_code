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

When using `docker-compose.host-network.yml`, Docker does not publish ports.
Instead, Django listens directly on the host network. In that mode,
`CEMP_HOST_PORT` is also used as the Django listen port, so choose a port that is
free on the host before starting the container.

If firewalld is enabled and remote browser access is required, open the selected
host port:

```bash
sudo firewall-cmd --add-port=18080/tcp --permanent
sudo firewall-cmd --reload
```

Verify both local and remote reachability:

```bash
curl -fsS http://127.0.0.1:18080/health/
ss -ltnp | grep ':18080 '
curl -fsS http://<server-ip-or-domain>:18080/health/
```

If the first two checks pass but the server IP check fails, the container is
running and the remaining issue is usually host firewall, campus firewall, or
network ACL policy.

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

The XGBoost version is pinned to `2.0.3` because the distributed polymer and
ionic-liquid model files were serialized with the XGBoost 2.0 model wrapper.
Changing this version can make a model load successfully but fail during
prediction because estimator attributes differ between releases.

The image also sets `LD_LIBRARY_PATH=/opt/conda/lib`. This keeps Pillow,
RDKit, PyTorch, XGBoost, and their compiled dependencies on the same Conda C++
runtime when several native libraries are imported in one process. Removing
this setting on older Linux hosts can produce a `GLIBCXX` symbol error even
when each package imports successfully in isolation.

If Docker bridge networking is broken on the host, use the host-network Compose
file instead:

```bash
docker compose -f docker-compose.host-network.yml up -d --build
```

This mode is intended for servers where Docker reports missing iptables
`DOCKER` chains during network creation. It avoids creating a bridge network and
binds Django directly to `CEMP_HOST_PORT` on the host.

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

Validate the demo login, public data API, and one model prediction:

```bash
BASE_URL=http://127.0.0.1:${CEMP_HOST_PORT:-8000}
TOKEN=$(curl -fsS -X POST "${BASE_URL}/api/token/" \
  -d "username=cemp_demo" \
  -d "password=cemp_demo_local" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["token"])')

curl -fsS "${BASE_URL}/polymer/api/public/experiment-polymer-data/?page_size=1"
curl -fsS -X POST "${BASE_URL}/ionic_liquid/api/similarity_search/" \
  -H "Content-Type: application/json" \
  -d '{"smiles":"CC(=O)[O-].CC[NH3+]","mol_type":"il","source":"experiment","topk":1,"method":"tanimoto"}'
curl -fsS -X POST "${BASE_URL}/polymer/api/polymer_predict_psmiles/" \
  -H "Authorization: Token ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"psmiles":"[*]CC[*]"}' \
  -o polymer_prediction_result.json
```

The final command also verifies that an API result can be exported to a local
JSON file. Run the complete release validator inside the container with:

```bash
docker compose exec cemp \
  python manage.py verify_public_release --manifest data/public_manifest.json
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

With `docker-compose.host-network.yml`, the open port is simply:

```text
<CEMP_HOST_PORT>/tcp on the Docker host
```

No Docker port publishing rule is created in host-network mode.

## CentOS 8 Validation Record

The public image was built and tested on CentOS Linux 8 on 2026-08-12 with
Docker Engine 26.1.3 and Docker Compose 5.1.4. Port `8000` was already in use on
the shared test host, so the validated service listened on `0.0.0.0:8001` by
setting `CEMP_HOST_PORT=8001` and using
`docker-compose.host-network.yml`. The validation covered migrations, demo data
loading, demo token authentication, public polymer data retrieval,
ionic-liquid similarity search, polymer and ionic-liquid model-backed
prediction, result-file export, and the release integrity command.

The same CentOS 8 container also loaded the complete `paper` CSV set into a
separate SQLite file without replacing the running demo database:

```bash
docker compose exec \
  -e CEMP_SQLITE_PATH=/tmp/cemp_paper_validation.sqlite3 \
  cemp python manage.py migrate --noinput
docker compose exec \
  -e CEMP_SQLITE_PATH=/tmp/cemp_paper_validation.sqlite3 \
  cemp python manage.py load_public_data \
    --manifest data/public_manifest.json --mode paper
```

The import loaded 231,187 database records. The verified core counts were
`IL=1,065`, `IL_ML_data=100,000`, `Cation_QC_data=3,774`,
`Anion_QC_data=2,220`, `experiment_polymer_data=13,116` rows and `21,402`
experimental property data points, `calculated_monomer_data=10,519`,
`calculated_polymer_data=1,000`, `BMS_experiment_result=39`, and
`Crystal=92,864`. The 213,581-row OMG polymer prediction CSV is intentionally
file-based and is verified by the manifest rather than imported into a Django
model.

This record documents one tested environment; `8001` is not a required CEMP
port. Any free TCP port can be selected through `CEMP_HOST_PORT`.

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

### Docker Bridge Network Cannot Be Created

Symptom:

```text
failed to create network ... iptables: No chain/target/match by that name
```

Fix options:

- restart Docker and retry the normal Compose file if you control the host;
- or use the host-network Compose file:

```bash
docker compose -f docker-compose.host-network.yml up -d --build
```

In host-network mode, set `CEMP_HOST_PORT` to the actual host port and update
`CEMP_ALLOWED_HOSTS`, `CEMP_CSRF_TRUSTED_ORIGINS`, and `CEMP_SITE_DOMAIN` to
match that port.

If Docker fails before Compose creates a network with a firewalld
`ZONE_CONFLICT`, first inspect the current assignment instead of deleting Docker
state:

```bash
sudo firewall-cmd --get-zone-of-interface=docker0
sudo firewall-cmd --get-active-zones
```

When `docker0` has been manually assigned to a zone that conflicts with the
Docker daemon's own firewalld integration, remove only that incorrect interface
assignment from the reported zone, both at runtime and permanently, and then
restart Docker. Do not delete `/var/lib/docker/network/files/local-kv.db` on a
shared host: it contains Docker network state used by existing containers.

If the daemon then reports multiple persisted networks with the same bridge
name, an administrator should inventory the existing Docker networks and repair
the daemon state during a maintenance window. The host-network Compose file can
be used with an isolated Docker daemon for non-destructive validation, but that
is an administrator operation rather than the normal CEMP deployment path.

### Compose Requires a Newer Buildx Plugin

Symptom:

```text
Docker Compose requires buildx ... or later
```

The preferred fix is to update the Docker Buildx plugin to the minimum version
reported by Compose. If package changes are not permitted, build the image with
the Docker legacy builder and let Compose start the prebuilt image:

```bash
DOCKER_BUILDKIT=0 docker build --network host -t cemp_public-cemp .
COMPOSE_PROJECT_NAME=cemp_public \
  docker compose -f docker-compose.host-network.yml up -d --no-build
```

The image name must match the Compose project and service naming convention:
`<project>-cemp` for service `cemp`.

### Service Listens Locally but Remote Access Fails

Symptoms:

```text
curl http://127.0.0.1:18080/health/  # works on the server
ss -ltnp | grep ':18080 '            # shows 0.0.0.0:18080
curl http://<server-ip>:18080/health/ # fails from another machine
```

Fixes:

- open the selected port in firewalld as root:

```bash
sudo firewall-cmd --add-port=18080/tcp --permanent
sudo firewall-cmd --reload
sudo firewall-cmd --list-ports
```

- if a Conda or Anaconda environment causes `firewall-cmd` D-Bus path errors,
  run the system command with a clean environment:

```bash
sudo env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/bin/firewall-cmd --add-port=18080/tcp --permanent
sudo env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/bin/firewall-cmd --reload
sudo env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/bin/firewall-cmd --list-ports
```

- if firewalld is already open, check upstream network policy or campus/VPN
  routing rules for the selected port.

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
