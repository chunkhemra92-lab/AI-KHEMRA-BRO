# Verification Notes — v6.4.1 Gemini Hardening

## Static Gemini hardening tests

The dedicated test suite passed. It verifies deduplicated key normalization, current and legacy encrypted-key decryption, invalid-key and quota classification, model fallback selection, API-key redaction in user-facing errors, JSON-mode configuration, immediate quota handling, and one bounded retry for a transient `503` error.

## Startup and original UI check

The Streamlit application started in a fresh process on local port 8504. The browser loaded the existing customer login page normally, with no import or startup exception. The user-facing login UI remains unchanged. No customer credential was entered, and no production API key was used during this check.

## Data-preservation behavior

The encryption layer first attempts to decrypt values using the current configured secret and then the v6.4 legacy secret. Therefore, adding a Streamlit `COOKIE_SECRET` later does not make existing encrypted customer API keys unreadable. New saves use the configured secret when present.

## Final reload check

After the final Gemini and key-storage changes, the local Streamlit application was reloaded in the browser. The original customer login UI rendered normally again without an import or startup error.
