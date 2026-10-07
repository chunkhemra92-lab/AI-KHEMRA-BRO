# AI KHEMRA BRO Smooth Khmer TTS Server

A standalone FastAPI service for generating polished Khmer MP3 clips. It is separate from Streamlit so TTS requests can run independently and do not block the customer UI.

## Voice roles

- `M` — `km-KH-PisethNeural`, natural adult male
- `F` — `km-KH-SreymomNeural`, natural adult female
- `M_THINK` — male inner thought, slightly slower/quieter
- `F_THINK` — female inner thought, slightly slower/quieter

The server keeps the voices close to native Edge Neural prosody, removes role metadata before speech, applies conservative clarity EQ, light compression, loudness normalization to `-16 LUFS`, true-peak limit at `-1.5 dB`, and no echo or stereo widening.

## API

- `GET /health` — health check
- `POST /v1/synthesize` — accepts ordered cues and returns a ZIP containing polished MP3 clips and `manifest.json`

Protect synthesis requests with `X-TTS-API-Key`.

## Deploy

Set the secret outside Git and run on a persistent host:

```bash
export TTS_API_KEY='random-long-tts-service-key'
docker compose up -d --build
curl http://127.0.0.1:8091/health
```

Port 8091 is bound to localhost by default. Put it behind HTTPS/reverse proxy before public use.

## Example request

```bash
curl -X POST http://127.0.0.1:8091/v1/synthesize \
  -H "X-TTS-API-Key: $TTS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "output_name":"khmer-dialogue",
    "cues":[
      {"id":1,"tag":"M","text":"សួស្តី អ្នកសុខសប្បាយទេ?"},
      {"id":2,"tag":"F","text":"ខ្ញុំសុខសប្បាយ អរគុណ។"},
      {"id":3,"tag":"M_THINK","text":"[M_THINK] ខ្ញុំត្រូវប្រុងប្រយ័ត្ន។"}
    ]
  }' -o khmer-dialogue.zip
```

The current Streamlit TTS path is intentionally unchanged until this service is deployed and verified. Then the app can be integrated through `TTS_SERVICE_URL` and `TTS_API_KEY` in a separate change.
