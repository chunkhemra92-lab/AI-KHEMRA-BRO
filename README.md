# AI KHEMRA BRO v6.7.12

AI KHEMRA BRO is a mobile-first Streamlit application for turning video dialogue or supplied subtitle text into translated SRT subtitles and dubbed MP3 audio. The **application interface is English-first**. It supports Khmer, English, Simplified Chinese, Korean, and Vietnamese output, while preserving the Khmer-specific subtitle and TTS rules required for natural Khmer dubbing.

## Production Files

Upload only these five files to the root of the Streamlit Community Cloud or Railway GitHub repository.

| File | Purpose |
|---|---|
| `app.py` | Complete Streamlit application, mobile UI, subtitle pipeline, and audio pipeline. |
| `requirements.txt` | Python dependencies installed by Streamlit Community Cloud or Railway. |
| `packages.txt` | System dependency declaration for `ffmpeg`. |
| `.gitignore` | Prevents databases, API keys, caches, and generated media from being committed. |
| `README.md` | Deployment and operating guidance. |

## Streamlit Secrets

Create the following secrets in Streamlit Community Cloud. **Never place API keys or passwords in `app.py`, GitHub, or this README.**

```toml
COOKIE_SECRET = "use-a-long-random-secret"
GEMINI_API_KEYS = "AIza..."
LICENSE_PEPPER = "use-a-separate-long-random-secret"
ADMIN_PASSWORD = "your-owner-password"
ADMIN_USERNAME = "KHEMRA"

# Optional: use only when rotating COOKIE_SECRET and migrating existing encrypted cookies.
# PREVIOUS_COOKIE_SECRETS = "previous-cookie-secret"
```

`GEMINI_API_KEYS` may contain multiple Gemini keys, one per line. If a key reaches a quota or has a temporary error, the application automatically attempts the next eligible key.

## Deploy to Streamlit Community Cloud

Place the five production files listed above in a GitHub repository. Create or update the Streamlit Community Cloud app, select that repository, and set `app.py` as the main file. Add the secrets before rebooting the application. Keep `COOKIE_SECRET` and `LICENSE_PEPPER` stable across updates so encrypted preferences and existing Access Codes remain valid.

## Deploy to Railway with Only These 5 Files

Upload the same five files above to the **root** of the GitHub repository connected to Railway. Do not upload the ZIP itself as one file, and do not delete `requirements.txt`.

In Railway, configure these values in the service dashboard instead of adding Docker or script files:

| Railway setting | Value |
|---|---|
| **Variable** | `RAILPACK_PYTHON_VERSION=3.12` |
| **Deploy Start Command** | `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true --browser.gatherUsageStats false` |
| **Variable** | `COOKIE_SECRET` = long random private value |
| **Variable** | `LICENSE_PEPPER` = a different long random private value |
| **Variable** | `ADMIN_USERNAME` and `ADMIN_PASSWORD` = Owner Dashboard credentials |
| **Variable** | `GEMINI_API_KEYS` = one or more Gemini keys, separated by newlines |
| **Variable** | `AI_KHEMRA_DATA_DIR=/data` |
| **Volume mount path** | `/data` |

The app reads Railway Variables privately at runtime. `pydub` is included in `requirements.txt` so Railway Railpack detects the required FFmpeg system package. Login, Access Code, subtitle translation, and TTS screens can start even if the host has a temporary faster-whisper import problem; only Video → SRT will then show a clear ASR dependency error. After deploy succeeds, choose **Settings → Networking → Public Networking → Generate Domain** to remove the “Unexposed service” status.

## Persistent Access Code Folder on Railway

Access Codes, customer names, expiry dates, plans, and audit records are stored in the separate database file `/data/licenses.db` when `AI_KHEMRA_DATA_DIR=/data` is set. Create one Railway **Volume** with mount path `/data` before creating production Access Codes. The Railway Volume is separate from the five code files, so normal GitHub/app updates replace `app.py` but keep your Access Code database.

Do not delete the `/data` Railway Volume, change its mount path, or remove `AI_KHEMRA_DATA_DIR=/data` during an update. Before any major migration, use **Owner Dashboard → API Key Status & Access Code Backup → Download Access Code Backup**. The backup lets the owner restore missing Access Codes if a storage service is ever replaced.

## Customer Access and Privacy

The owner creates one manually chosen Access Code per customer. A valid code may be used again after logout, a browser close, a phone restart, or on another phone; the app does not device-lock customers. Each browser or phone keeps its own Gemini keys, target-language preference, selected model, and translation style in encrypted browser storage. A separate device never reads or writes another device’s personal API key or Settings through the shared license database.

The Owner Dashboard does not reveal any API key values. It can show whether server-side Gemini keys are available, create and renew customer codes, enable or disable access, and export or restore Access Code backups.

## Docker VPS Persistent Storage

For Docker/VPS deployment, set `AI_KHEMRA_DATA_DIR=/data`. The provided Docker Compose configuration mounts `/data` as a persistent Docker volume, so the Access Code database survives container rebuilds and VPS reboots. See `DEPLOY_VPS_UBUNTU.md` in the VPS bundle for HTTPS, auto-restart, backup, and update instructions.

## Shared CPU/RAM Protection

The application reuses one cached Whisper model instead of loading a model for every customer request. It also protects the two memory-intensive media paths—video transcription and MP3 creation—with one shared media slot per application process. This prevents simultaneous FFmpeg, Whisper, and audio-mastering jobs from exhausting the server’s CPU or RAM.

Translation-only SRT requests remain concurrent because they primarily use Gemini API/network capacity. If another customer is already processing a video or generating MP3 audio, the next media request is safely refused after a short wait, without exposing or changing anyone else’s files, settings, or output. The customer can wait briefly and try again. Each session continues to use its own private temporary workspace.

For high-volume public use across multiple server instances, a shared external job queue and dedicated worker service are required; the built-in guard protects one Streamlit application process.

## Scaling from 1,000 to 10,000 Users

This package supports independent browser sessions and does not device-lock an Access Code. Each phone/browser receives a random session workspace, and personal API keys and Settings stay in that browser’s encrypted storage. This prevents customer files, SRT text, MP3 bytes, and personal preferences from being mixed in one application process.

A single Streamlit application with its local `licenses.db` file must not be represented as a 10,000-user multi-server system. For genuine multi-instance scale, migrate the shared state before adding replicas:

| Scale layer | Required production component | Purpose |
|---|---|---|
| Customer accounts and Access Codes | One shared managed relational database | Ensures every app instance validates the same active code and expiry state. |
| Videos, SRTs, and MP3s | Private object storage with per-job paths and short-lived download links | Keeps customer media out of local server disks and prevents one job from reading another job’s files. |
| Whisper, FFmpeg, and TTS work | Shared job queue plus dedicated media workers | Limits expensive media work globally, rather than only inside one web process. |
| Web interface | Stateless app replicas behind HTTPS load balancing | Allows many phones to sign in and use the interface without sharing browser session memory. |
| Secrets and auditing | Centralized secret management and structured audit logs | Protects owner credentials/API keys and makes access events traceable. |

Do not place the same SQLite `licenses.db` file on multiple replicas. SQLite is suitable for a single application process and owner backup/restore, not for a 1,000–10,000-user shared production database.

## Owner Backup and Restore

Before an update or reboot, open **API Key Status & Access Code Backup** in the Owner Dashboard and download the Access Code backup. The backup includes customer names, Access Codes, plans, and expiry dates, but **never includes API keys**.

If a hosting update does not retain the prior `licenses.db`, upload that backup with **Restore Missing Codes**. Restore adds only codes that are missing. It never overwrites, deletes, regenerates, or exposes existing codes.

> Do not rotate `COOKIE_SECRET` or `LICENSE_PEPPER` without a planned migration. These values protect encrypted customer settings and the hashes used to validate existing Access Codes.

## Settings and Workflows

The visible **AI Translate Controller** presents the Gemini model, target language, translation style, source language, workflow, processing mode, 4G Lite Mode, API-key entry, Clear Video, and Save & Apply controls in one ordered mobile panel. Its temporary close button does not change any saved preference; use **Open Controller** to show it again. The target language, Gemini model, and translation style remain private to the signed-in customer.

| Workflow | Result |
|---|---|
| **Automatic Khmer SRT** | Extracts dialogue from the video and returns a translated, tagged SRT. |
| **Khmer SRT + MP3** | Generates the translated SRT and then produces its dubbed MP3. |
| **Source SRT only** | Extracts the source-language SRT without translation. |
| **AI Subtitle Translator** | Translates a pasted source SRT while retaining its original cue IDs and timestamps. |
| **SRT → Speech** | Creates a tagged multi-voice MP3 from an existing SRT. |
| **Text → Speech** | Creates a single-voice MP3 from target-language text. |

For faster uploads, use an MP4 at 720p or 480p and under 100 MB. Video processing accepts MP4, MOV, MKV, and WEBM files up to 10 minutes. Lite Mode reduces the maximum file size to 60 MB for more reliable mobile and 4G use.

**Fast Processing Mode** uses faster Whisper ASR settings and groups up to 60 short subtitle cues in one Gemini request, compared with 50 cues in Higher Accuracy Mode. This can reduce Gemini request round trips for longer SRT files while retaining the same Six-Rule Translation Brain, voice-tag validation, target-language validation, repair handling, and locked SRT IDs/timestamps. Actual elapsed time still depends on video length, server CPU availability, Gemini model response time, network conditions, and API quota.

## Six-Rule Translation Brain and SRT Timing

All translation paths use the Six-Rule Translation Brain. It produces natural spoken dialogue, preserves character relationships and emotional intent, keeps lines concise for subtitle timing, applies one supported speaker tag per cue, and enforces the selected target language.

The application keeps SRT cue IDs and timestamps locked. Before output, it verifies that a translation did not change the original cue order, IDs, start times, or end times. Invalid timing is reported as an error rather than silently altered.

## Voice Tags and Thought Voices

Each subtitle cue must begin with one of the following tags.

| Tag | Use |
|---|---|
| `[M]` | Male dialogue spoken aloud. |
| `[F]` | Female dialogue spoken aloud. |
| `[M_THINK]` | Male inner thought that other characters cannot hear. |
| `[F_THINK]` | Female inner thought that other characters cannot hear. |

`[M_THINK]` and `[F_THINK]` are rendered at **60% of normal dialogue volume**: a 40% reduction that keeps inner thoughts clearly audible while distinguishing them from spoken dialogue. In v6.7.10, thought speech also uses a clearly calmer pace, gentle pitch shift, and a warm, narrower speech band, so it no longer sounds like ordinary dialogue. Thought voices do not add echo or reverb. The audio pipeline retains natural phrasing, avoids forced speed increases, applies gentle cue joins where appropriate, and performs final loudness leveling.

## Do Not Upload

Do not commit or upload `licenses.db`, `.streamlit/secrets.toml`, private videos, generated MP3 files, or API keys to GitHub. The included `.gitignore` protects these files, but repository contents should always be checked before deployment.
