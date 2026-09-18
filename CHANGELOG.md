# Changelog

## v6.5.2 — Complete Gemini 2.5–3.8 translation model catalog

This patch exposes the full supported text-translation catalog to every signed-in user: Gemini 2.5 Flash, 2.5 Flash-Lite, 2.5 Pro, Gemini 3 Flash Preview, 3.1 Flash-Lite, 3.1 Pro Preview, 3.5 Flash, 3.5 Flash-Lite, 3.6 Flash, 3.7 Flash, and 3.8 Flash. Live voice and TTS-only endpoints are intentionally excluded from the text translator.

Every translation batch preserves input cue IDs and retries missing output lines before failing, so a successful translation cannot silently omit subtitle text.

## v6.5.1 — Gemini 3.8 Flash integration

This patch adds official Google AI Studio / Gemini API model `gemini-3.8-flash` as the preferred translation model. Existing Gemini model options remain available as automatic fallbacks for older or restricted API keys.

The model supports text, image, video, audio, and PDF inputs with text output, structured outputs, function calling, search grounding, and up to 1,048,576 input tokens according to the [official Gemini model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).

## v6.5 — Stability release

This release standardizes the application version at **6.5** and adds a reproducible development dependency set for release validation. Runtime dependency pins remain unchanged from the previously verified baseline; no unvalidated production behavior or deployment target is changed by this scoped release.

### Validation scope

- Source-level safeguards and application stability assertions.
- Audio, subtitle timing, language, voice, theme, and deployment package checks already present in the repository.
- Python compilation and version consistency checks.

### Deployment note

These GitHub releases are versioned source releases, not automatic production deployments. Before deploying, create a backup of the production license database, build from the tagged commit, verify the Streamlit health endpoint, and run one complete video-to-Khmer-SRT-to-MP3 workflow.
