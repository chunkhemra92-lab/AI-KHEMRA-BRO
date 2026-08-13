# Verification Notes — v6.4.3 Video and Gemini Stability

## Test suite

The application passed Python syntax checking, the existing Khmer SRT/tag rule suite, the Gemini hardening suite, and a new local video stability suite. The local video suite created a short MP4 with FFmpeg, saved a permitted uploaded-video object, rejected an unsupported suffix, extracted a valid 16 kHz mono audio track, and verified fenced JSON-array parsing.

## Startup check

A fresh Streamlit process on local port 8506 loaded the original customer login interface in the browser without import or startup errors. No production API key or customer credential was used.

## Scope of changes

The v6.4.3 hardening preserves the original UI, existing account data, and stored API-key behavior. It adds guarded upload writes, zero-length upload detection, bounded FFmpeg logs and errors, audio-file validation, finite Gemini video-context polling, corrected JSON-fence parsing, and safe cleanup if upload persistence fails.
