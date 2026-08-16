# AI KHEMRA BRO v6.2

Main fix: Gemini model compatibility for Video → Whisper → Khmer SRT → MP3.

- Defaults to `gemini-3.5-flash-lite`.
- Automatic fallback to other supported Flash models.
- Keeps Chinese source transcription separate from Khmer SRT.
- MP3 generation requires valid Khmer subtitle text.

Deploy by replacing `app.py`, keeping `requirements.txt` and `packages.txt`, then redeploying the service.

## Optional reference-voice cloning

The application now includes an optional **Reference Voice Clone** upload in the audio controls. When a reference MP3/WAV and, ideally, its exact transcript are provided, the app can use the optional `VoxCPM2-Khmer` backend to preserve the reference speaker's timbre while generating new Khmer lines. Install the optional dependencies with `pip install -r requirements-voice-clone.txt` on a machine with a compatible NVIDIA GPU, then restart the app. The standard Edge TTS path remains the default when no reference file is uploaded.

The reference-cloning mode is serialized because the model is memory-intensive. It applies the same reference timbre to all SRT tags; `[M]`, `[F]`, `[M_THINK]`, and `[F_THINK]` continue to control role processing and inner-thought style. Voice cloning is an approximation and must not be represented as guaranteed 100% identity reproduction. Use only reference audio for which you have permission, and disclose AI-generated speech where appropriate.
