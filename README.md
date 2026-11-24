# MATLY MOVIE STORE

MATLY MOVIE STORE is a Streamlit marketplace for publishing movies, selling access with coins, and letting customers watch titles they have purchased. The former translation, subtitle, voice-generation, model, and generated-code workflows have been removed.

## Features

- Movie catalog with search, genres, featured titles, posters, and video links.
- Customer profiles with persistent coin wallets and purchased libraries.
- Top-up requests that an admin approves after payment confirmation.
- Admin Studio for publishing titles, setting prices, marking HOT titles, and reviewing top-ups.
- SQLite persistence under `STORE_DATA_DIR`.

## Run locally

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export ADMIN_USERNAME=owner
export ADMIN_PASSWORD='use-a-long-password'
streamlit run app.py
```

Customers enter a display name in the sidebar. Admin access uses the username and password from the environment.

## Docker deployment

```bash
cp .env.example .env
# Set DOMAIN, ACME_EMAIL, ADMIN_PASSWORD and payment contact values.
docker compose up -d --build
docker compose logs --tail=100 app
```

The SQLite database is stored in the `ai_khemra_data` volume. Use video URLs from authorized storage/CDN and publish only content for which you have distribution rights.
