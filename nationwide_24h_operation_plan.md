# AI KHEMRA BRO — 24-hour nationwide operation plan

## Decision summary

AI KHEMRA BRO can be made available to people throughout Cambodia through its public URL, but the present Streamlit Community Cloud deployment must **not** be treated as a guaranteed 24-hour production service. Community Cloud automatically hibernates an app after 12 hours without traffic and its shared resource limits can throttle or stop workloads that exceed capacity.[1]

The application code is now better prepared for production use: it has bounded Edge TTS concurrency, FFmpeg timeouts, SQLite write-contention settings, temporary-file cleanup, a strict 150 MB video boundary, and regression tests. However, continual nationwide availability also requires a persistent host, durable database, durable object storage, monitoring, and API quota planning.

## What has already been hardened

| Area | Current protection |
|---|---|
| Audio generation | Edge TTS is limited to two simultaneous requests and includes bounded retry behavior. |
| Video and audio jobs | FFmpeg conversions and final mixing have explicit time limits; temporary processing files are cleaned automatically. |
| Upload safety | The Streamlit server and application both enforce a 150 MB upload limit. |
| Access-code writes | SQLite uses WAL mode and a 30-second busy timeout to reduce short write-contention failures. |
| Quality control | Regression tests cover Settings stability, theme preference, translations, four voice roles, subtitle timing, FFmpeg mixing, and Edge TTS retry behavior. |

## What must change for a genuine 24-hour public service

| Requirement | Current position | Production action |
|---|---|---|
| Always-on web service | Community Cloud can sleep after 12 inactive hours.[1] | Use a paid persistent or minimum-instance hosting service; keep the Streamlit server continuously running. |
| Durable Access Code database | `licenses.db` is a local SQLite file beside the app. | Move licenses, saved settings, and audit records to managed PostgreSQL or MySQL with automated backups. |
| Durable large files | Video processing uses temporary local folders. | Store uploaded videos and finished MP3/SRT outputs in object storage, with expiry rules to control cost. |
| Multi-user capacity | faster-whisper and FFmpeg are CPU/RAM-intensive; one video job can occupy the app process. | Use a job queue and separate worker processes; set per-user concurrency and upload quotas. |
| API continuity | Gemini and Edge TTS can impose provider quotas or temporary limits. | Keep multiple approved API keys, monitor failures, set spending/quota alerts, and provide clear retry messages. |
| Visibility and recovery | Public hosting needs fast detection of errors. | Add uptime checks, central logs, error alerts, daily database backups, and a tested restore procedure. |
| Public identity and security | The current URL is a Streamlit subdomain. | Use a custom domain with HTTPS, keep secrets in the host’s secret manager, and rotate access credentials periodically. |

## Recommended rollout

The safest path is to treat the current deployment as a **pilot** and keep it for design and workflow validation. For nationwide production, deploy the same Streamlit application in a Docker-capable environment with at least two isolated components: a web service for login, Settings, uploads, and results; and a worker service for Whisper, FFmpeg, and Edge TTS jobs. The two services should share a managed relational database and object storage rather than local files.

A production launch should begin with controlled access-code distribution and a small concurrent-user limit. Monitor actual processing duration, error rate, memory use, queue length, Gemini quota failures, and Edge TTS failures for one to two weeks. Increase worker capacity only after the observed load is stable.

> The present code hardening improves reliability, but no code change alone can turn a sleeping shared-host deployment and a local SQLite file into a nationwide 24-hour service. The required remaining decision is the production hosting and managed-data environment.

## Immediate next action needed from the owner

Choose one of the following directions before migration work begins.

| Choice | Suitable use |
|---|---|
| Keep Streamlit Community Cloud | Testing and limited pilot use only; no 24-hour guarantee. |
| Move to managed production hosting | Recommended for 24-hour public access; requires a hosting account, managed database, object storage, and deployment configuration. |
| Run on an always-on server you control | Suitable if you already have a reliable server administrator, backups, monitoring, and a fixed public domain. |

## References

[1] [Streamlit Community Cloud — Manage your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app): Resource limits and 12-hour inactive-app hibernation policy.
