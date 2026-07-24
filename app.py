
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import streamlit as st

# Optional imports are checked at runtime so the UI can show a friendly message.
try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None

try:
    from google import genai
except Exception:
    genai = None

try:
    import edge_tts
except Exception:
    edge_tts = None


# ============================================================
# APP CONFIGURATION
# ============================================================

APP_NAME = "Ai KHEMRA BRO"
APP_SUBTITLE = "CHINESE DRAMA → KHMER AI DUBBING WORKSTATION"
WORK_ROOT = Path(os.getenv("WORK_ROOT", tempfile.gettempdir())) / "ai_khemra_bro"
WORK_ROOT.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "200"))
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEFAULT_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
DEFAULT_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

VOICE_MAP = {
    "M": "km-KH-PisethNeural",
    "F": "km-KH-SreymomNeural",
    "M_YOUNG": "km-KH-PisethNeural",
    "F_YOUNG": "km-KH-SreymomNeural",
    "M_ADULT": "km-KH-PisethNeural",
    "F_ADULT": "km-KH-SreymomNeural",
    "M_OLD": "km-KH-PisethNeural",
    "F_OLD": "km-KH-SreymomNeural",
    "BOY": "km-KH-PisethNeural",
    "GIRL": "km-KH-SreymomNeural",
    "M_THINK": "km-KH-PisethNeural",
    "F_THINK": "km-KH-SreymomNeural",
    "NARRATOR_M": "km-KH-PisethNeural",
    "NARRATOR_F": "km-KH-SreymomNeural",
}

ALLOWED_SPEAKER_TAGS = list(VOICE_MAP)
ALLOWED_EMOTION_TAGS = [
    "NEUTRAL", "HAPPY", "SAD", "ANGRY", "FEAR",
    "LOVE", "SARCASM", "CRYING", "THINKING"
]

SUPPORTED_MEDIA = [
    "mp4", "mkv", "mov", "avi", "webm",
    "mp3", "wav", "m4a", "ogg", "aac", "flac"
]


# ============================================================
# DATA TYPES
# ============================================================

@dataclass
class Cue:
    index: int
    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return max(0.05, self.end - self.start)


# ============================================================
# GENERAL UTILITIES
# ============================================================

def run_command(
    command: list[str],
    *,
    timeout: int = 600,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a subprocess safely and return stdout/stderr."""
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{detail}")
    return result


def require_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(
            f"Missing required program: {name}. "
            f"Install FFmpeg and make sure '{name}' is on PATH."
        )


def safe_name(filename: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("._")
    return stem or "media"


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def session_folder() -> Path:
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex
    folder = WORK_ROOT / st.session_state.session_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def clear_session_files() -> None:
    folder = session_folder()
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)

    keep = {"session_id"}
    for key in list(st.session_state.keys()):
        if key not in keep:
            del st.session_state[key]


def save_upload(uploaded_file) -> Path:
    data = uploaded_file.getvalue()
    digest = hash_bytes(data)
    suffix = Path(uploaded_file.name).suffix.lower()
    output = session_folder() / f"source_{digest}{suffix}"
    if not output.exists():
        output.write_bytes(data)
    return output


def media_duration(path: Path) -> float:
    require_binary("ffprobe")
    result = run_command([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("Could not determine media duration.") from exc


def extract_audio(source: Path, destination: Path) -> Path:
    require_binary("ffmpeg")
    run_command([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(source),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(destination),
    ])
    return destination


def is_video(path: Path) -> bool:
    return path.suffix.lower() in {".mp4", ".mkv", ".mov", ".avi", ".webm"}


def seconds_to_srt(value: float) -> str:
    value = max(0.0, value)
    total_ms = int(round(value * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def srt_to_seconds(value: str) -> float:
    match = re.fullmatch(
        r"\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*", value
    )
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value}")
    h, m, s, ms = map(int, match.groups())
    return h * 3600 + m * 60 + s + ms / 1000.0


def cues_to_srt(cues: Iterable[Cue]) -> str:
    blocks = []
    for n, cue in enumerate(cues, start=1):
        text = cue.text.strip()
        blocks.append(
            f"{n}\n"
            f"{seconds_to_srt(cue.start)} --> {seconds_to_srt(cue.end)}\n"
            f"{text}"
        )
    return "\n\n".join(blocks).strip() + "\n"


def parse_srt(content: str) -> list[Cue]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    blocks = re.split(r"\n{2,}", normalized)
    cues: list[Cue] = []
    time_pattern = re.compile(
        r"(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
        r"(\d{1,2}:\d{2}:\d{2}[,.]\d{3})"
    )

    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue

        if lines[0].strip().isdigit():
            index = int(lines[0].strip())
            time_line_index = 1
        else:
            index = len(cues) + 1
            time_line_index = 0

        match = time_pattern.search(lines[time_line_index])
        if not match:
            continue

        start = srt_to_seconds(match.group(1))
        end = srt_to_seconds(match.group(2))
        text = "\n".join(lines[time_line_index + 1:]).strip()
        if end <= start:
            end = start + 0.25
        cues.append(Cue(index=index, start=start, end=end, text=text))

    for idx, cue in enumerate(cues, start=1):
        cue.index = idx
    return cues


def strip_voice_tags(text: str) -> str:
    text = re.sub(r"^\s*\[[A-Z_]+\]\s*", "", text)
    text = re.sub(r"^\s*\[[A-Z_]+\]\s*", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def speaker_from_text(text: str, mode: str) -> str:
    if mode == "All Male":
        return "M"
    if mode == "All Female":
        return "F"

    match = re.match(r"\s*\[([A-Z_]+)\]", text)
    if match and match.group(1) in VOICE_MAP:
        return match.group(1)
    return "M"


def clean_model_output(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:srt|text|json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


# ============================================================
# WHISPER TRANSCRIPTION
# ============================================================

@st.cache_resource(show_spinner=False)
def load_whisper_model(model_name: str, compute_type: str):
    if WhisperModel is None:
        raise RuntimeError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        )
    return WhisperModel(
        model_name,
        device="auto",
        compute_type=compute_type,
    )


def transcribe_audio(
    audio_path: Path,
    model_name: str,
    compute_type: str,
    source_language: str,
) -> list[Cue]:
    model = load_whisper_model(model_name, compute_type)
    language = None if source_language == "Auto Detect" else {
        "Chinese": "zh",
        "English": "en",
        "Thai": "th",
        "Vietnamese": "vi",
    }.get(source_language)

    segments, _info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=300,
            speech_pad_ms=250,
        ),
        condition_on_previous_text=True,
        word_timestamps=False,
    )

    cues: list[Cue] = []
    for index, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        if text:
            cues.append(Cue(index, float(segment.start), float(segment.end), text))
    return cues


# ============================================================
# GEMINI TRANSLATION AND SPEAKER LABELING
# ============================================================

def build_translation_prompt(
    cues: list[Cue],
    translation_style: str,
    voice_mode: str,
) -> str:
    source_srt = cues_to_srt(cues)

    speaker_rule = {
        "Auto": (
            "Detect the likely speaker and prefix every dialogue line with exactly "
            "one speaker tag from this list: "
            + ", ".join(f"[{x}]" for x in ALLOWED_SPEAKER_TAGS)
            + ". Keep the same character's tag stable across nearby cues. "
            "Use THINK tags for inner thoughts and NARRATOR tags for narration."
        ),
        "All Male": "Prefix every dialogue line with [M].",
        "All Female": "Prefix every dialogue line with [F].",
    }[voice_mode]

    style_rule = {
        "Chinese Drama Pro": (
            "Use natural spoken Khmer suitable for Chinese historical/fantasy drama dubbing. "
            "Preserve rank, relationship, emotion, humor, threats, affection, and context. "
            "Use suitable Khmer forms of address for emperor, empress, master, elder, general, "
            "young master, servant, senior and junior. Do not translate mechanically."
        ),
        "100% Audio Sync": (
            "Use concise natural spoken Khmer. Keep each translated cue short enough to fit "
            "inside its original time window while preserving the core meaning and emotion."
        ),
        "Standard": (
            "Translate into clear, natural, grammatically correct spoken Khmer."
        ),
    }[translation_style]

    return f"""
You are an expert Chinese-drama subtitle translator and Khmer dubbing director.

TASK
Translate the SRT below into natural Khmer.

STRICT RULES
1. Preserve every cue number and timestamp exactly.
2. Do not merge, delete, reorder, or split cues.
3. Return valid SRT only. No Markdown and no explanation.
4. Remove all Chinese characters from the translated dialogue.
5. Keep dialogue readable and reasonably short.
6. Preserve names unless a natural Khmer phonetic spelling is needed.
7. {speaker_rule}
8. {style_rule}
9. Add one emotion tag after the speaker tag only when clearly useful, chosen from:
   {", ".join(f"[{x}]" for x in ALLOWED_EMOTION_TAGS)}
   Example: [F][SAD] ខ្ញុំមិនអាចត្រឡប់ទៅវិញបានទេ។
10. Never change timestamps.

SOURCE SRT
{source_srt}
""".strip()


def split_cues_for_translation(cues: list[Cue], max_chars: int = 9000) -> list[list[Cue]]:
    groups: list[list[Cue]] = []
    current: list[Cue] = []
    current_size = 0

    for cue in cues:
        approximate = len(cue.text) + 80
        if current and current_size + approximate > max_chars:
            groups.append(current)
            current = []
            current_size = 0
        current.append(cue)
        current_size += approximate

    if current:
        groups.append(current)
    return groups


def translate_with_gemini(
    cues: list[Cue],
    api_key: str,
    model_name: str,
    translation_style: str,
    voice_mode: str,
    progress_callback=None,
) -> list[Cue]:
    if genai is None:
        raise RuntimeError(
            "google-genai is not installed. Run: pip install google-genai"
        )
    if not api_key.strip():
        raise RuntimeError("Please enter a Gemini API key in the sidebar.")

    client = genai.Client(api_key=api_key.strip())
    groups = split_cues_for_translation(cues)
    translated: list[Cue] = []

    for group_index, group in enumerate(groups, start=1):
        prompt = build_translation_prompt(group, translation_style, voice_mode)
        last_error: Optional[Exception] = None

        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                raw = clean_model_output(response.text or "")
                parsed = parse_srt(raw)

                if len(parsed) != len(group):
                    raise RuntimeError(
                        f"AI returned {len(parsed)} cues, expected {len(group)}."
                    )

                # Restore original cue numbering and timestamps unconditionally.
                for original, new in zip(group, parsed):
                    translated.append(
                        Cue(
                            index=original.index,
                            start=original.start,
                            end=original.end,
                            text=new.text.strip(),
                        )
                    )
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(2 ** attempt)

        if last_error:
            raise RuntimeError(
                f"Translation failed in batch {group_index}/{len(groups)}: {last_error}"
            )

        if progress_callback:
            progress_callback(group_index, len(groups))

    return translated


# ============================================================
# EDGE TTS + AUDIO TIMING
# ============================================================

def atempo_filter(speed: float) -> str:
    """Build FFmpeg atempo chain. Each stage must be between 0.5 and 2.0."""
    speed = max(0.25, min(4.0, speed))
    factors = []
    remaining = speed
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    while remaining < 0.5:
        factors.append(0.5)
        remaining /= 0.5
    factors.append(remaining)
    return ",".join(f"atempo={factor:.6f}" for factor in factors)


async def edge_save(
    text: str,
    voice: str,
    output: Path,
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> None:
    if edge_tts is None:
        raise RuntimeError("edge-tts is not installed. Run: pip install edge-tts")
    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
    )
    await communicator.save(str(output))


def run_async(coro):
    """Run async code safely from Streamlit."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    return asyncio.run(coro)


def synthesize_one_cue(
    cue: Cue,
    voice_mode: str,
    output_dir: Path,
    sync_mode: str,
) -> Path:
    require_binary("ffmpeg")
    require_binary("ffprobe")

    speaker = speaker_from_text(cue.text, voice_mode)
    voice = VOICE_MAP.get(speaker, VOICE_MAP["M"])
    spoken_text = strip_voice_tags(cue.text) or "..."

    raw_mp3 = output_dir / f"raw_{cue.index:05}.mp3"
    fitted_wav = output_dir / f"fit_{cue.index:05}.wav"

    run_async(edge_save(spoken_text, voice, raw_mp3))
    generated_duration = max(0.05, media_duration(raw_mp3))
    target_duration = max(0.10, cue.duration)

    # speed > 1 means faster playback.
    speed = generated_duration / target_duration
    if sync_mode == "Speed Up Only":
        speed = max(1.0, speed)

    # Avoid extreme unnatural processing.
    speed = max(0.70, min(1.80, speed))
    filter_chain = atempo_filter(speed)

    run_command([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_mp3),
        "-af", filter_chain,
        "-ar", "48000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(fitted_wav),
    ])

    # Trim or pad to the exact cue duration.
    exact_wav = output_dir / f"cue_{cue.index:05}.wav"
    run_command([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(fitted_wav),
        "-af", f"apad=pad_dur={target_duration:.3f}",
        "-t", f"{target_duration:.3f}",
        "-ar", "48000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(exact_wav),
    ])
    return exact_wav


def create_silence(duration: float, output: Path) -> Path:
    require_binary("ffmpeg")
    duration = max(0.01, duration)
    run_command([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi",
        "-i", "anullsrc=r=48000:cl=mono",
        "-t", f"{duration:.3f}",
        "-c:a", "pcm_s16le",
        str(output),
    ])
    return output


def generate_dubbed_audio(
    cues: list[Cue],
    voice_mode: str,
    sync_mode: str,
    total_duration: float,
    progress_callback=None,
) -> Path:
    if not cues:
        raise RuntimeError("No SRT cues available.")

    root = session_folder() / "tts"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)

    timeline_parts: list[Path] = []
    cursor = 0.0

    for number, cue in enumerate(cues, start=1):
        if cue.start > cursor:
            silence = root / f"silence_{number:05}.wav"
            create_silence(cue.start - cursor, silence)
            timeline_parts.append(silence)

        audio = synthesize_one_cue(cue, voice_mode, root, sync_mode)
        timeline_parts.append(audio)
        cursor = max(cursor, cue.end)

        if progress_callback:
            progress_callback(number, len(cues))

    if total_duration > cursor:
        ending = root / "silence_end.wav"
        create_silence(total_duration - cursor, ending)
        timeline_parts.append(ending)

    concat_file = root / "concat.txt"
    concat_file.write_text(
        "\n".join(
            "file '" + str(path.resolve()).replace("'", "'\\''") + "'"
            for path in timeline_parts
        ),
        encoding="utf-8",
    )

    output_mp3 = session_folder() / "khmer_dubbed_audio.mp3"
    run_command([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-ar", "48000",
        str(output_mp3),
    ], timeout=1800)

    return output_mp3


def merge_video_and_audio(video: Path, audio: Path) -> Path:
    require_binary("ffmpeg")
    output = session_folder() / "khmer_dubbed_video.mp4"
    run_command([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video),
        "-i", str(audio),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output),
    ], timeout=1800)
    return output


# ============================================================
# STREAMLIT UI
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root {
  --bg: #090c12;
  --card: #111722;
  --card2: #182231;
  --text: #f6f7fb;
  --muted: #aeb7c5;
  --purple: #cf00ff;
  --cyan: #62def8;
  --green: #13d994;
}
.stApp {
  background: var(--bg);
  color: var(--text);
}
.block-container {
  max-width: 1080px;
  padding-top: 1.5rem;
  padding-bottom: 5rem;
}
.hero {
  border: 3px solid var(--purple);
  border-top: 0;
  border-radius: 0 0 32px 32px;
  background: linear-gradient(180deg,#131417,#101216);
  padding: 38px 22px 42px;
  text-align: center;
  box-shadow: 0 0 28px rgba(207,0,255,.12);
  margin-bottom: 28px;
}
.hero h1 {
  font-size: clamp(34px,6vw,58px);
  margin: 0;
  font-weight: 850;
}
.hero p {
  color: var(--cyan);
  letter-spacing: 3px;
  font-weight: 800;
  margin-top: 22px;
}
.step-title {
  font-size: clamp(32px,5vw,52px);
  font-weight: 850;
  margin-top: 25px;
  margin-bottom: 15px;
}
.status-box {
  background: #0d1c30;
  border-radius: 16px;
  padding: 18px 22px;
  font-size: 20px;
  margin: 12px 0 20px;
}
.success-box {
  background: #064f3c;
  border: 2px solid #0be2a4;
  border-radius: 16px;
  padding: 18px 22px;
  font-size: 20px;
  color: #22e4aa;
  margin: 12px 0 20px;
}
div.stButton > button, div.stDownloadButton > button {
  min-height: 64px;
  border-radius: 15px;
  font-size: 20px;
  font-weight: 800;
  border: 0;
  background: linear-gradient(90deg,#b700f4,#df00ff);
  color: white;
}
div.stButton > button:disabled {
  opacity: .38;
}
textarea {
  font-family: "Noto Sans Khmer", "Khmer OS System", sans-serif !important;
  font-size: 18px !important;
  line-height: 1.65 !important;
}
[data-testid="stSidebar"] {
  background: #111827;
}
.small-muted {
  color: var(--muted);
  font-size: 14px;
}
</style>
""",
    unsafe_allow_html=True,
)

# Session defaults
defaults = {
    "source_path": None,
    "source_hash": None,
    "duration": 0.0,
    "source_srt": "",
    "khmer_srt": "",
    "audio_path": None,
    "video_path": None,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)


with st.sidebar:
    st.title("⚙️ ការកំណត់")

    st.subheader("🌍 Target Language")
    st.selectbox("Select Language", ["Khmer (ខ្មែរ)"], disabled=True)

    st.subheader("🎭 Translation Style")
    translation_style = st.radio(
        "ជ្រើសរើសរបៀបបកប្រែ",
        ["Chinese Drama Pro", "100% Audio Sync", "Standard"],
        index=0,
    )

    st.subheader("⚙️ Audio Sync Mode")
    sync_mode = st.radio(
        "កំណត់ល្បឿនសំឡេង",
        ["Speed Up Only", "Speed Up & Slow Down"],
        index=0,
    )

    st.subheader("🗣️ Voice Mode")
    voice_mode = st.radio(
        "កំណត់សំឡេង",
        ["Auto", "All Male", "All Female"],
        index=0,
    )

    st.subheader("🧠 AI Model")
    gemini_model = st.text_input("Gemini model", value=DEFAULT_GEMINI_MODEL)
    whisper_model = st.selectbox(
        "Whisper model",
        ["tiny", "base", "small", "medium", "large-v3", "turbo"],
        index=["tiny", "base", "small", "medium", "large-v3", "turbo"].index(
            DEFAULT_WHISPER_MODEL
            if DEFAULT_WHISPER_MODEL in ["tiny", "base", "small", "medium", "large-v3", "turbo"]
            else "small"
        ),
    )
    compute_type = st.selectbox(
        "Whisper compute type",
        ["int8", "float16", "float32"],
        index=0,
    )

    st.subheader("🔑 API Key")
    api_key = st.text_input(
        "Gemini API key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="The key stays in this browser session and is not written into the project files.",
    )

    st.caption(
        "Do not paste your API key into screenshots or public code. "
        "For deployment, use a secret environment variable."
    )


st.markdown(
    f"""
<div class="hero">
  <h1>{APP_NAME}</h1>
  <p>{APP_SUBTITLE}</p>
</div>
""",
    unsafe_allow_html=True,
)

tab_video, tab_srt, tab_speech = st.tabs([
    "🎬 AI Video Dubbing",
    "🌐 AI SRT Translator",
    "📜 Subtitle to Speech",
])

with tab_video:
    st.markdown('<div class="step-title">1️⃣ Generate Subtitles (Khmer)</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload Chinese drama video or audio",
        type=SUPPORTED_MEDIA,
        accept_multiple_files=False,
        help=f"Maximum recommended upload: {MAX_UPLOAD_MB} MB",
    )

    source_language = st.selectbox(
        "Source language",
        ["Chinese", "Auto Detect", "English", "Thai", "Vietnamese"],
        index=0,
    )

    if uploaded is not None:
        if uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
            st.error(f"File is larger than {MAX_UPLOAD_MB} MB.")
        else:
            current_hash = hash_bytes(uploaded.getvalue())
            if st.session_state.source_hash != current_hash:
                path = save_upload(uploaded)
                st.session_state.source_path = str(path)
                st.session_state.source_hash = current_hash
                st.session_state.duration = media_duration(path)
                st.session_state.source_srt = ""
                st.session_state.khmer_srt = ""
                st.session_state.audio_path = None
                st.session_state.video_path = None

            path = Path(st.session_state.source_path)
            if is_video(path):
                st.video(str(path))
            else:
                st.audio(str(path))

            st.caption(
                f"File: {uploaded.name} • "
                f"Duration: {st.session_state.duration:.1f} seconds • "
                f"Size: {uploaded.size / 1024 / 1024:.1f} MB"
            )

    generate_subtitles = st.button(
        "🚀 Generate Subtitles (Sync 100%)",
        use_container_width=True,
        disabled=not st.session_state.source_path,
    )

    if generate_subtitles:
        try:
            source = Path(st.session_state.source_path)
            audio_wav = session_folder() / "source_audio.wav"

            status = st.empty()
            progress = st.progress(0)

            status.markdown('<div class="status-box">🎧 Extracting clean audio…</div>', unsafe_allow_html=True)
            extract_audio(source, audio_wav)
            progress.progress(12)

            status.markdown('<div class="status-box">🧠 Transcribing original dialogue…</div>', unsafe_allow_html=True)
            original_cues = transcribe_audio(
                audio_wav,
                whisper_model,
                compute_type,
                source_language,
            )
            if not original_cues:
                raise RuntimeError("No speech was detected in the uploaded media.")
            st.session_state.source_srt = cues_to_srt(original_cues)
            progress.progress(35)

            status.markdown('<div class="status-box">🌐 Translating into natural Khmer…</div>', unsafe_allow_html=True)

            def translation_progress(done: int, total: int) -> None:
                value = 35 + int(60 * done / max(1, total))
                progress.progress(min(value, 95))

            khmer_cues = translate_with_gemini(
                original_cues,
                api_key,
                gemini_model,
                translation_style,
                voice_mode,
                translation_progress,
            )
            st.session_state.khmer_srt = cues_to_srt(khmer_cues)
            progress.progress(100)
            status.markdown('<div class="success-box">✅ SRT Generation Complete!</div>', unsafe_allow_html=True)
        except Exception as exc:
            st.error(str(exc))

    st.subheader("Generated SRT from Video")
    edited_srt = st.text_area(
        "ពិនិត្យ និងកែសម្រួលអត្ថបទ SRT មុនបង្កើតសំឡេង",
        value=st.session_state.khmer_srt,
        height=440,
        key="khmer_editor",
        placeholder="Khmer SRT will appear here…",
    )
    if edited_srt != st.session_state.khmer_srt:
        st.session_state.khmer_srt = edited_srt

    if st.session_state.khmer_srt.strip():
        st.download_button(
            "⬇️ Download Khmer SRT",
            data=st.session_state.khmer_srt.encode("utf-8-sig"),
            file_name="khmer_subtitles.srt",
            mime="application/x-subrip",
            use_container_width=True,
        )

    st.markdown('<div class="step-title">2️⃣ AI Dubbing (Edge TTS Studio)</div>', unsafe_allow_html=True)

    generate_audio = st.button(
        "🎙️ Generate Dubbed Audio (MP3)",
        use_container_width=True,
        disabled=not st.session_state.khmer_srt.strip(),
    )

    if generate_audio:
        try:
            cues = parse_srt(st.session_state.khmer_srt)
            if not cues:
                raise RuntimeError("The SRT editor does not contain valid cues.")

            progress = st.progress(0)
            status = st.empty()
            status.markdown('<div class="status-box">🔊 Preparing Khmer AI voices…</div>', unsafe_allow_html=True)

            total_duration = st.session_state.duration or max(c.end for c in cues)

            def tts_progress(done: int, total: int) -> None:
                progress.progress(int(done * 100 / max(1, total)))
                status.markdown(
                    f'<div class="status-box">🎙️ Generating Khmer voice ({done}/{total})…</div>',
                    unsafe_allow_html=True,
                )

            output_audio = generate_dubbed_audio(
                cues,
                voice_mode,
                sync_mode,
                total_duration,
                tts_progress,
            )
            st.session_state.audio_path = str(output_audio)
            status.markdown('<div class="success-box">✅ Khmer MP3 is ready!</div>', unsafe_allow_html=True)
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.audio_path and Path(st.session_state.audio_path).exists():
        audio_path = Path(st.session_state.audio_path)
        st.audio(str(audio_path))
        st.download_button(
            "⬇️ Download Khmer MP3",
            data=audio_path.read_bytes(),
            file_name="khmer_dubbed_audio.mp3",
            mime="audio/mpeg",
            use_container_width=True,
        )

        if st.session_state.source_path and is_video(Path(st.session_state.source_path)):
            if st.button("🎬 Merge Khmer Voice + Original Video", use_container_width=True):
                try:
                    with st.spinner("Merging video and Khmer audio…"):
                        output_video = merge_video_and_audio(
                            Path(st.session_state.source_path),
                            audio_path,
                        )
                        st.session_state.video_path = str(output_video)
                    st.success("Dubbed video is ready.")
                except Exception as exc:
                    st.error(str(exc))

    if st.session_state.video_path and Path(st.session_state.video_path).exists():
        video_path = Path(st.session_state.video_path)
        st.video(str(video_path))
        st.download_button(
            "⬇️ Download Dubbed MP4",
            data=video_path.read_bytes(),
            file_name="khmer_dubbed_video.mp4",
            mime="video/mp4",
            use_container_width=True,
        )

    st.divider()
    if st.button("🗑️ Clear Video Project", use_container_width=True):
        clear_session_files()
        st.rerun()


with tab_srt:
    st.markdown('<div class="step-title">🌐 Translate Existing SRT into Khmer</div>', unsafe_allow_html=True)

    srt_upload = st.file_uploader(
        "Upload Chinese SRT",
        type=["srt", "txt"],
        key="srt_upload",
    )

    source_srt_text = ""
    if srt_upload is not None:
        source_srt_text = srt_upload.getvalue().decode("utf-8-sig", errors="replace")

    source_srt_text = st.text_area(
        "Chinese SRT",
        value=source_srt_text,
        height=330,
        key="source_srt_manual",
    )

    if st.button(
        "🌐 Translate SRT to Khmer",
        use_container_width=True,
        disabled=not source_srt_text.strip(),
    ):
        try:
            cues = parse_srt(source_srt_text)
            if not cues:
                raise RuntimeError("No valid SRT cues found.")

            progress = st.progress(0)

            def callback(done: int, total: int) -> None:
                progress.progress(int(done * 100 / max(1, total)))

            result = translate_with_gemini(
                cues,
                api_key,
                gemini_model,
                translation_style,
                voice_mode,
                callback,
            )
            st.session_state.translated_srt_tab = cues_to_srt(result)
            st.success("Translation complete.")
        except Exception as exc:
            st.error(str(exc))

    translated_srt_tab = st.text_area(
        "Khmer SRT",
        value=st.session_state.get("translated_srt_tab", ""),
        height=420,
        key="translated_srt_tab_editor",
    )
    st.session_state.translated_srt_tab = translated_srt_tab

    if translated_srt_tab.strip():
        st.download_button(
            "⬇️ Download Translated SRT",
            data=translated_srt_tab.encode("utf-8-sig"),
            file_name="translated_khmer.srt",
            mime="application/x-subrip",
            use_container_width=True,
        )


with tab_speech:
    st.markdown('<div class="step-title">📜 Khmer Subtitle to Speech</div>', unsafe_allow_html=True)

    speech_srt_upload = st.file_uploader(
        "Upload Khmer SRT",
        type=["srt", "txt"],
        key="speech_srt_upload",
    )

    speech_text = ""
    if speech_srt_upload is not None:
        speech_text = speech_srt_upload.getvalue().decode("utf-8-sig", errors="replace")

    speech_text = st.text_area(
        "Khmer SRT with speaker tags",
        value=speech_text,
        height=420,
        key="speech_srt_editor",
        placeholder="[M] សួស្តី...\n[F] ចាស...",
    )

    speech_duration = st.number_input(
        "Final audio duration in seconds (0 = use last SRT timestamp)",
        min_value=0.0,
        value=0.0,
        step=1.0,
    )

    if st.button(
        "🎙️ Create MP3 from SRT",
        use_container_width=True,
        disabled=not speech_text.strip(),
    ):
        try:
            cues = parse_srt(speech_text)
            if not cues:
                raise RuntimeError("No valid SRT cues found.")
            total = speech_duration if speech_duration > 0 else max(c.end for c in cues)
            progress = st.progress(0)

            def callback(done: int, count: int) -> None:
                progress.progress(int(done * 100 / max(1, count)))

            output = generate_dubbed_audio(
                cues,
                voice_mode,
                sync_mode,
                total,
                callback,
            )
            st.session_state.speech_audio_path = str(output)
            st.success("MP3 created.")
        except Exception as exc:
            st.error(str(exc))

    speech_audio_path = st.session_state.get("speech_audio_path")
    if speech_audio_path and Path(speech_audio_path).exists():
        p = Path(speech_audio_path)
        st.audio(str(p))
        st.download_button(
            "⬇️ Download Speech MP3",
            data=p.read_bytes(),
            file_name="subtitle_speech.mp3",
            mime="audio/mpeg",
            use_container_width=True,
        )


st.caption(
    "Processing runs on the server, not on the phone. Keep API keys in deployment secrets. "
    "Translation and speaker detection should always be reviewed before publishing."
)
