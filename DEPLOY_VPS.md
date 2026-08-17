# Deploy AI KHEMRA BRO on Your Own VPS

This package runs the current AI KHEMRA BRO Streamlit application as an always-on Docker service with FFmpeg/FFprobe, faster-whisper, a persistent SQLite data volume, and a Caddy HTTPS reverse proxy. The design preserves the existing application workflow and is suitable for a **single VPS** deployment.

> **Important:** This is a reliable single-server deployment, not high availability. It keeps the current SQLite design on a durable Docker volume. For multi-server nationwide scale, follow the separate PostgreSQL/object-storage/worker migration plan before running more than one application replica.

## 1. VPS prerequisites

Use a 64-bit Ubuntu VPS with a public IPv4 address. The AI media pipeline needs CPU and memory for FFmpeg and faster-whisper; start with at least **4 vCPU and 8 GB RAM** for a modest public launch, then measure queue time and resource use before increasing capacity. Install Docker Engine and the Docker Compose plugin by following Docker’s official Linux installation documentation. Ensure ports **80**, **443**, and SSH are allowed by the VPS firewall.

Before startup, create DNS records for your chosen domain. For example, point the `A` record for `app.yourdomain.com` to your VPS public IPv4 address. Caddy obtains and renews TLS certificates automatically only after this DNS record points to the server.

## 2. Copy application files and protect secrets

Clone your private repository on the VPS, then enter the project directory.

```bash
git clone https://github.com/chunkhemra92-lab/AI-KHEMRA-BRO.git ai-khemra-bro
cd ai-khemra-bro
cp .env.example .env
chmod 600 .env
```

Edit `.env` only on the VPS. Do not commit this file. Set `DOMAIN` and `ACME_EMAIL`, create a strong owner password, and generate long random values for `ADMIN_ROUTE_TOKEN`, `COOKIE_SECRET`, and `LICENSE_PEPPER`.

```bash
openssl rand -hex 48
```

Use the generated values for `COOKIE_SECRET` and `LICENSE_PEPPER`. If you have existing active users, copy the **same** `COOKIE_SECRET` and `LICENSE_PEPPER` from the current deployment. Changing either value may invalidate Access Code verification or make encrypted saved settings/API-key records unreadable.

## 3. Start the production services

Build and start the Streamlit app and HTTPS proxy.

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f app
```

The `app` service is available only inside the Docker network on port 8501. The `caddy` service is the only public entry point and listens on ports 80 and 443. Do **not** open port 8501 in the VPS firewall.

After Caddy obtains the certificate, browse to:

```text
https://YOUR_DOMAIN
```

## 4. Confirm health and persistent data

Check the health endpoint and running containers.

```bash
docker compose ps
curl -fsS https://YOUR_DOMAIN/_stcore/health
```

The `ai_khemra_data` Docker volume persists `licenses.db`; the `ai_khemra_models` volume preserves downloaded faster-whisper model files. These volumes must not be deleted during normal updates.

```bash
docker volume ls | grep ai_khemra
```

## 5. Import an existing license database

If you have a trusted copy of the current `licenses.db`, stop the app first and copy it into the persistent volume before the first public launch. Keep an encrypted backup of the source file. The target file must be readable and writable by the container’s application user.

```bash
docker compose down
# Copy the verified database into the Docker volume using a temporary helper container.
docker run --rm \
  -v ai-khemra-bro_ai_khemra_data:/data \
  -v "$(pwd)":/import:ro \
  alpine sh -c 'cp /import/licenses.db /data/licenses.db && chown 10001:10001 /data/licenses.db'
docker compose up -d
```

The volume name includes the Compose project name. If your directory has a different name, run `docker volume ls` and substitute the displayed volume name. Validate an owner login and one existing customer Access Code after import before announcing the new URL.

## 6. Backup procedure

Take a daily encrypted backup of the SQLite database and keep it outside the VPS. Run the following manually before automating it with a protected scheduled task.

```bash
mkdir -p backups
docker run --rm \
  -v ai-khemra-bro_ai_khemra_data:/data:ro \
  -v "$(pwd)/backups":/backup \
  alpine sh -c 'cp /data/licenses.db /backup/licenses-$(date +%F).db'
```

Test restoring a backup on a non-production VPS before relying on it. For multi-server or higher-traffic deployments, migrate from SQLite to managed PostgreSQL as described in `production_migration_plan_24_7.md`.

## 7. Safe update procedure

Before every update, back up the database and inspect the current service status. Then pull the intended Git commit and rebuild the app image.

```bash
docker compose ps
git fetch origin
git checkout main
git pull --ff-only
docker compose up -d --build
docker compose logs --tail=100 app
```

If a deployment fails, return to the previous Git commit and rebuild.

```bash
git log --oneline -5
git checkout PREVIOUS_COMMIT_SHA
docker compose up -d --build
```

## 8. Operational checks

| Check | Command or action | Frequency |
|---|---|---|
| Container health | `docker compose ps` | Daily |
| Application logs | `docker compose logs --tail=100 app` | Daily and after errors |
| TLS/domain response | `curl -I https://YOUR_DOMAIN` | Daily |
| License database backup | Copy and encrypt `licenses.db` from the data volume | Daily |
| Disk space | `df -h` and `docker system df` | Weekly |
| Test deployment | Use a staging VPS or maintenance window before major updates | Every release |

## Security rules

Keep `.env`, database backups, Docker volumes, and API keys private. Use SSH keys rather than password logins for the VPS, restrict the firewall to SSH/80/443, keep Ubuntu and Docker updated, and use strong unique owner credentials. Never expose the Docker daemon or Streamlit port 8501 directly to the internet.

## References

[1] [Streamlit — Deploy using Docker](https://docs.streamlit.io/deploy/tutorials/docker): Streamlit containerization, port, and health-check guidance.

[2] [Docker Engine install documentation](https://docs.docker.com/engine/install/): Official Docker installation instructions for Linux servers.
