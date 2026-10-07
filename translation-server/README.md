# AI KHEMRA BRO Translation Server

A standalone FastAPI translation service for SRT cues. It is separate from Streamlit so translation load, retries, and Gemini API calls do not block the customer UI.

## API

- `GET /health` — health check
- `POST /v1/translate` — translate ordered SRT cues

The request requires `X-Translation-API-Key`. The response preserves every cue ID and returns `id`, `tag`, and `text` in the original order.

## Speed design

- Sends up to 60 cues per Gemini request by default.
- Runs up to 3 batches concurrently by default.
- Retries transient Gemini errors with short exponential backoff.
- Uses `gemini-3.8-flash` by default; override with `TRANSLATION_MODEL`.
- Tune `TRANSLATION_MAX_WORKERS` from 2–4 depending on Gemini quota. Higher values can trigger rate limits.

## Deploy

Set secrets outside Git, then run on a persistent host:

```bash
export TRANSLATION_API_KEY='random-long-service-key'
export GEMINI_API_KEY='your-google-ai-studio-key'
docker compose up -d --build
curl http://127.0.0.1:8090/health
```

For a public connection, place it behind HTTPS and keep port 8090 private. Do not put `GEMINI_API_KEY` in the client or Streamlit browser code.

## Example request

```bash
curl -X POST http://127.0.0.1:8090/v1/translate \
  -H "X-Translation-API-Key: $TRANSLATION_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "target_language":"Khmer (ខ្មែរ)",
    "style":"Natural movie dialogue",
    "cues":[
      {"id":1,"start":"00:00:01,000","end":"00:00:03,000","source":"Good morning.","input_tag":"AUTO"}
    ]
  }'
```

The current Streamlit translation path is intentionally unchanged until this server is deployed and verified. After that, the app can be configured with `TRANSLATION_SERVICE_URL` and `TRANSLATION_API_KEY` as a separate integration change.
