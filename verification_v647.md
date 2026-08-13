# Verification Notes — v6.4.7

The app compiled successfully after the waiting-card, bulk Access Code, and voice-tempo changes. Local Streamlit startup on port 8509 loaded the existing customer login page with no startup error.

The automated bulk-code test created 1,000 unique sequential codes (`KHBR-0001` through `KHBR-1000`) in a temporary SQLite database, verified that the next batch starts after the existing sequence, and verified the 1,000-code validation limit. The test also confirmed the main video workflow no longer renders the jumping percentage/time strings used by the former waiting display.

The existing regression tests for Gemini, SRT, video processing, browser-session isolation, and live Edge TTS will be rerun before release.

## Final regression suite

The final suite passed Gemini JSON/retry/fallback checks, Khmer SRT/tag checks, video upload and FFmpeg audio extraction checks, browser-session isolation checks, live Edge TTS generation, the 1,000-code batch creation check, calm-waiting UI source checks, and Python syntax compilation.

The live application loaded the customer login UI after a fresh local startup on port 8509 with no startup error.
