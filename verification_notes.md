# Verification Notes — v6.4.6 Natural Voice and User Isolation

## Automated checks

The regression suite passed Python syntax checking, Gemini retry/JSON/key fallback simulation, Khmer SRT/tag validation, video upload and FFmpeg extraction, and the new browser-session isolation test. The isolation test confirms that switching from one Access Code to another in the same browser removes the first user's temporary SRT, MP3 bytes, video workspace, preview text, and personal API-key state before creating a fresh workspace.

## Voice checks

Thought profiles are now only modestly slower, lower, and softer than normal dialogue. Their FFmpeg chain no longer contains `aecho`; it keeps a mild low-pass treatment only. The output master uses a narrower loudness range to reduce abrupt level swings between cues.

## Startup check

A fresh Streamlit process on local port 8508 loaded the existing customer-login interface with no import or startup error.

## Scope boundary

Temporary work and browser-stored personal API keys are isolated per browser/session. The separate `GEMINI_API_KEYS` Streamlit Secret is intentionally app-wide and must be treated as an owner-controlled shared fallback, not as a customer's private key. The local SQLite license database is not a production-grade shared database for a guaranteed 1,000 concurrent video jobs; such a volume requires durable external storage and a compute/deployment architecture sized for concurrent video processing.
