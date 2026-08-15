# AI KHEMRA BRO v6.7.3

AI KHEMRA BRO is a mobile-first Streamlit application for turning video dialogue or supplied subtitle text into translated SRT subtitles and dubbed MP3 audio. The **application interface is English-first**. It supports Khmer, English, Simplified Chinese, Korean, and Vietnamese output, while preserving the Khmer-specific subtitle and TTS rules required for natural Khmer dubbing.

## Production Files

Upload only these five files to the root of the Streamlit Community Cloud repository.

| File | Purpose |
|---|---|
| `app.py` | Complete Streamlit application, mobile UI, subtitle pipeline, and audio pipeline. |
| `requirements.txt` | Python dependencies installed by Streamlit Community Cloud. |
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

## Customer Access and Privacy

The owner creates one manually chosen Access Code per customer. A valid code may be used again after logout, a browser close, a phone restart, or on another phone; the app does not device-lock customers. Each customer’s Gemini keys, target-language preference, selected model, and translation style are stored privately through encrypted browser storage with a customer-specific encrypted database fallback.

The Owner Dashboard does not reveal any API key values. It can show whether server-side Gemini keys are available, create and renew customer codes, enable or disable access, and export or restore Access Code backups.

## Owner Backup and Restore

Before an update or reboot, open **API Key Status & Access Code Backup** in the Owner Dashboard and download the Access Code backup. The backup includes customer names, Access Codes, plans, and expiry dates, but **never includes API keys**.

If a hosting update does not retain the prior `licenses.db`, upload that backup with **Restore Missing Codes**. Restore adds only codes that are missing. It never overwrites, deletes, regenerates, or exposes existing codes.

> Do not rotate `COOKIE_SECRET` or `LICENSE_PEPPER` without a planned migration. These values protect encrypted customer settings and the hashes used to validate existing Access Codes.

## Settings and Workflows

Open **☰ Settings** to select the Gemini model, target language, translation style, source language, workflow, and processing mode. The target language, Gemini model, and translation style are private to the signed-in customer.

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

`[M_THINK]` and `[F_THINK]` are rendered at **60% of normal dialogue volume**: a 40% reduction that keeps inner thoughts clearly audible while distinguishing them from spoken dialogue. Thought voices do not add echo or reverb. The audio pipeline retains natural phrasing, avoids forced speed increases, applies gentle cue joins where appropriate, and performs final loudness leveling.

## Do Not Upload

Do not commit or upload `licenses.db`, `.streamlit/secrets.toml`, private videos, generated MP3 files, or API keys to GitHub. The included `.gitignore` protects these files, but repository contents should always be checked before deployment.
