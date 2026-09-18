# AI KHEMRA BRO v6.5.1

AI KHEMRA BRO is a Streamlit application for the **Video → Whisper → Khmer SRT → MP3** workflow. It uses Gemini for translation and subtitle generation, faster-whisper for transcription, FFmpeg for media processing, and Edge TTS for Khmer voice output.

> **Version note:** This README documents the v6.5.1 Gemini 3.8 Flash integration patch. Runtime dependency pins remain unchanged from the verified v6.5 baseline; validate the tagged commit before any production deployment.

## Runtime highlights

- Gemini model compatibility with automatic Flash-model fallback.
- Google AI Studio / Gemini API support with `gemini-3.8-flash` as the preferred model and older-model fallback for compatible keys.
- Separate source transcription and Khmer subtitle generation.
- Khmer subtitle validation before MP3 generation.
- Multi-voice audio processing with FFmpeg.
- Persistent SQLite license data for Docker deployments.
- Persistent faster-whisper model storage in Docker deployments.

## Run locally

Install the system dependency listed in `packages.txt` (FFmpeg), create a Python 3.12 environment, install the Python dependencies, and start Streamlit:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Create a local `.env` from `.env.example` when local configuration is required. Keep secrets, API keys, license databases, generated media, and session data outside Git.

## Docker deployment

The production deployment uses Docker Compose with an app container and a Caddy HTTPS reverse proxy:

```bash
cp .env.example .env
chmod 600 .env
# Edit .env and set DOMAIN, ACME_EMAIL, and strong secret values.
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 app
```

The app listens internally on port `8501`. Caddy is the public entry point on ports `80` and `443`. Docker volumes preserve the license database and downloaded faster-whisper models. Follow [DEPLOY_VPS.md](DEPLOY_VPS.md) for the complete VPS procedure, backup guidance, and rollback steps.

## v6.5 release checklist

Before calling a deployment v6.5, verify all of the following:

1. Confirm `APP_VERSION` in `app.py` is `6.5`.
2. Review and test the pinned runtime dependencies in `requirements.txt`.
3. Run the source checks and the relevant audio, subtitle-timing, language, and deployment tests.
4. Build the Docker image from a clean checkout and confirm that the image contains only runtime files. Development tests, audit scripts, historical reports, and generated metrics are excluded by `.dockerignore`.
5. Confirm the Streamlit health endpoint and test one complete video-to-Khmer-SRT-to-MP3 workflow.
6. Back up the production license database before deployment.
7. Install the development validation dependencies and run the checks:

```bash
pip install -r requirements-dev.txt
for test in test_*.py; do python "$test"; done
```

8. Tag the verified commit, for example:

```bash
git tag -a v6.5 -m "AI KHEMRA BRO v6.5"
git push origin v6.5
```

## Mobile repository setup

The expected mobile repository name is:

```text
https://github.com/chunkhemra92-lab/ai-khemra-bro-mobile
```

At the time of writing, GitHub does not resolve this repository for the authenticated `chunkhemra92-lab` account. The setup commands below should be run after the repository is created or the correct owner/repository name is confirmed.

### Check GitHub CLI access

```bash
gh auth status
gh repo view chunkhemra92-lab/ai-khemra-bro-mobile
```

The account that owns or administers the repository should show an `ADMIN` permission. For a collaborator, the repository owner must invite the GitHub username with the minimum required role:

- **Read/Triage:** view and review code only.
- **Write:** push branches and create changes.
- **Maintain:** manage most repository settings without full administration.
- **Admin:** manage access, settings, webhooks, and repository configuration.

Grant **Admin** only to a trusted repository owner or maintainer. Use **Write** for normal development whenever possible.

### Clone and configure the mobile repository

After access is available:

```bash
gh repo clone chunkhemra92-lab/ai-khemra-bro-mobile
cd ai-khemra-bro-mobile
git status --short --branch
git remote -v
```

Before connecting the mobile client to the v6.5 backend, configure the API base URL through the mobile project’s environment mechanism (for example, an `.env` file or platform-specific config). Do not hard-code private API keys, owner passwords, license secrets, or signing credentials in the mobile repository.

Use separate development and production endpoints, test authentication and upload behavior against a non-production deployment first, and commit only non-secret example configuration such as `.env.example`.

### Mobile release handoff

For a v6.5 mobile release, confirm that:

- The mobile client points to the verified v6.5 backend endpoint.
- Khmer subtitle text and generated audio are rendered correctly on supported devices.
- Upload, timeout, retry, and error states are tested on a real network.
- No secrets or generated media are committed.
- The mobile repository has branch protection and at least one review requirement before production releases.

## Repository hygiene

Runtime files are kept in the repository, while development-only tests and historical engineering artifacts are excluded from production Docker build contexts. The `.gitignore` protects local secrets, SQLite files, generated media, and temporary session data.

## License and security

Keep `.env`, API keys, license databases, backups, Docker volumes, and signing credentials private. If a secret is exposed, rotate it immediately and review repository history. Never expose Streamlit port `8501` directly to the public internet when using the VPS deployment; use the Caddy reverse proxy and HTTPS configuration instead.
