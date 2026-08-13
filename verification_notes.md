# Verification Notes — v6.4.5 Voice and Secrets

## Automated checks

The full suite passed: Gemini JSON/retry/key fallback simulation, Khmer SRT/tag validation, video upload and FFmpeg extraction, thought-voice filter validation, Streamlit `GEMINI_API_KEYS` fallback normalization, and live Edge-TTS Khmer profile generation for normal and thought voice profiles. No customer Gemini API key was used.

## Thought-voice distinction

The test confirms that `[M_THINK]` and `[F_THINK]` use a slower, lower, softer profile and a separate FFmpeg chain with a low-pass filter and light echo. Ordinary `[M]` and `[F]` do not receive that echo chain.

## Startup check

A fresh Streamlit process started on local port 8507 and loaded the existing customer-login interface normally, with no import or startup error. The UI structure remains unchanged.
