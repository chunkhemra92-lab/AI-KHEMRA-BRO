# Changelog

## v6.5.13 — Authoritative License Server login routing

- Added optional remote License Server routing for Owner Code creation and customer login validation.
- When `LICENSE_SERVICE_URL` is configured, the remote License Server is the single source of truth; Streamlit no longer rejects Codes created by that server as “invalid”.
- Added a small local shadow record after successful validation so account-bound settings and session display continue to work without sharing the License database.
- Preserved the existing local database fallback when the remote License Server is not configured.

## v6.5.12 — Natural Khmer audio and translation validation

- Added conservative `dynaudnorm` smoothing on the voice bus, final master, and standalone TTS output to reduce cue-to-cue loudness jumps without removing natural emotion.
- Kept the existing gentle tempo range (`0.86x–1.18x`), centered dry dialogue, light compression, and `-16 LUFS` final master target.
- Added Khmer-script validation to Gemini/Google translation acceptance paths so non-Khmer or mixed Chinese output is rejected before TTS.
- Normalized accepted Google translation text before it reaches the dubbing engine.

## v6.5.11 — Simplified speech settings

Removes the confusing Speech Provider dropdown from Settings. The customer workflow now uses the single built-in Edge TTS route with the four locked Khmer voice roles; the backend compatibility functions remain private and are not exposed as user choices.

## Isolated Smooth Khmer TTS Server package

Adds a separate `tts-server/` FastAPI service using the four locked Khmer Neural voice roles, conservative clarity processing, `-16 LUFS` loudness normalization, no echo/stereo widening, retries, and parallel cue rendering. Streamlit remains unchanged until the service is deployed and verified.

## Isolated Translation Server package

Adds a separate `translation-server/` FastAPI service that batches up to 60 subtitle cues and processes up to 3 Gemini requests concurrently with retry handling. Streamlit remains unchanged until the service is deployed and verified.

## Isolated License Server package

Adds a standalone `license-server/` FastAPI service with its own persistent SQLite volume and protected endpoints for Access Code creation, validation, renewal, listing, and revocation. The Streamlit app is intentionally unchanged until the service is deployed and its API URL and service key are configured.

## v6.5.10 — Exact-term Access Code expiry

The generated Code card now expires exactly with the selected license term. When an Access Code reaches `expires_at`, login is rejected and the license is automatically disabled; the Owner must renew it or issue a new Code.

## v6.5.9 — One-year Access Code retention

Keeps the newly generated customer Access Code card available for 365 days instead of 24 hours. The actual license expiry still follows the duration selected by the Owner, including the 1-year option.

## v6.5.8 — Empty login placeholders

Removes the Khmer name hint and the `KHBR-XXXX-XXXX` access-code hint from the login inputs so both fields remain visually clean and empty until the user types.

## v6.5.7 — Clean customer login fields

Refines the customer sign-in form with clear Username and Password / Access Code labels, taller rounded inputs, improved contrast, and mobile-friendly spacing while preserving the existing Access Code authentication logic.

## v6.5.6 — Natural four-role Khmer voice polish

Tunes the four locked roles—normal male, normal female, male inner thought, and female inner thought—for native Khmer Neural prosody. Removes artificial echo and Haas widening from inner thoughts, keeps speech centered and dry, reduces aggressive pitch/rate offsets, and limits timing correction to a safer 0.86–1.18× range.

## v6.5.5 — Simplified SRT editor controls

Removes the **ពិនិត្យ SRT** validation button and **ស្តារវិញ** restore button from the editor toolbar while keeping the SRT editor and remaining generation/download workflow intact. Restores the earlier customer sign-in appearance with the branded hero card and original login layout.

## v6.5.4 — Always-visible video preview

Removes the optional **Video Preview** checkbox. Uploaded videos now display automatically in the Video → SRT workflow whenever the upload is valid.

## v6.5.3 — PyAV compatibility fix

Pins PyAV to the compatible `<19` range for `faster-whisper==1.2.1`. PyAV 19 removed the `metadata_errors` argument used by the decoder, which caused video transcription to fail before Gemini translation or audio generation began.

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
