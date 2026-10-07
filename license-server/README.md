# AI KHEMRA BRO License Server

A standalone Access Code service. It owns its own SQLite database and does not read or write the Streamlit application's `licenses.db`.

## What it provides

- `GET /health` — health check
- `POST /v1/licenses` — create a Code (admin key)
- `GET /v1/licenses` — list Codes without exposing raw Codes (admin key)
- `POST /v1/licenses/validate` — validate a Code from the Streamlit app (service key)
- `POST /v1/licenses/{id}/renew` — renew a Code (admin key)
- `POST /v1/licenses/{id}/revoke` — immediately disable a Code (admin key)

License terms are exact: 7, 30, 90, 180, or 365 days. A Code is automatically invalidated on its expiry check.

## Run on a persistent VPS

Set three strong secrets in the shell or in your deployment secret manager; do not commit them:

```bash
export LICENSE_PEPPER='random-long-secret-used-for-hashing'
export LICENSE_ADMIN_KEY='random-long-admin-api-key'
export LICENSE_SERVICE_KEY='random-long-app-api-key'
docker compose up -d --build
curl http://127.0.0.1:8080/health
```

The database is stored in the named volume `ai_khemra_license_data`. Back it up before upgrades:

```bash
docker run --rm -v ai-khemra-bro-license_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/license-db-backup.tgz -C /data .
```

## Create a one-year Code

```bash
curl -X POST http://127.0.0.1:8080/v1/licenses \
  -H "X-License-Admin-Key: $LICENSE_ADMIN_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"customer_name":"Customer Name","duration_days":365}'
```

The generated raw Code is returned only at creation/renewal time. The service should be placed behind HTTPS/reverse proxy before connecting a public Streamlit app.

## Integration note

The current Streamlit app remains unchanged and continues using its existing local license database. This isolation prevents the new service from disrupting the live app. The next integration step is to configure Streamlit with `LICENSE_SERVICE_URL` and `LICENSE_SERVICE_KEY`, then switch customer validation and Owner CRUD to these API endpoints after the server is deployed and tested.
