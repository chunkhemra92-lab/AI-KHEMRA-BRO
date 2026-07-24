from __future__ import annotations

import asyncio
import json
import os
import re
import secrets
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import edge_tts
import streamlit as st

try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None

try:
    from google import genai
except Exception:
    genai = None


# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(
    page_title="AI KHEMRA BRO",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebarCollapsedControl"],
#MainMenu,
footer,
.stDeployButton,
[data-testid="manage-app-button"] {
    display: none !important;
}
.block-container { padding-top: 1.2rem !important; max-width: 980px; }
.hero {
    border: 3px solid #d900ff; border-radius: 36px; padding: 42px 20px;
    text-align: center; background: #12131a; margin-bottom: 18px;
}
.hero h1 { margin: 0; font-size: clamp(2.1rem, 7vw, 4.2rem); }
.hero p { color: #57d8ff; font-weight: 800; letter-spacing: 2px; }
.card {
    background: #101c2b; border: 1px solid #22598a; border-radius: 24px;
    padding: 20px; margin: 14px 0;
}
.ok { background:#063f32; border:1px solid #00c997; border-radius:18px; padding:16px; }
.warn { background:#3b2310; border:1px solid #ffb020; border-radius:18px; padding:16px; }
.small { color:#9ba8ba; font-size:.92rem; }
.stButton > button, .stDownloadButton > button {
    border-radius: 16px !important; min-height: 52px; font-weight: 800;
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# CONSTANTS / DATA MODELS
# =========================================================
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEFAULT_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "60"))
MAX_VIDEO_MINUTES = int(os.getenv("MAX_VIDEO_MINUTES", "10"))

MALE_VOICE = "km-KH-PisethNeural"
FEMALE_VOICE = "km-KH-SreymomNeural"

VOICE_PROFILES = {
    "BOY": {"voice": MALE_VOICE, "rate": "+10%", "pitch": "+28Hz"},
    "GIRL": {"voice": FEMALE_VOICE, "rate": "+10%", "pitch": "+24Hz"},
    "MAN": {"voice": MALE_VOICE, "rate": "+0%", "pitch": "+0Hz"},
    "WOMAN": {"voice": FEMALE_VOICE, "rate": "+0%", "pitch": "+0Hz"},
    "OLD_MAN": {"voice": MALE_VOICE, "rate": "-12%", "pitch": "-18Hz"},
    "OLD_WOMAN": {"voice": FEMALE_VOICE, "rate": "-12%", "pitch": "-14Hz"},
}

TAG_PATTERN = re.compile(r"^\s*\[(BOY|GIRL|MAN|WOMAN|OLD_MAN|OLD_WOMAN)\]\s*", re.I)
TIME_PATTERN = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


@dataclass
class SubtitleItem:
    index: int
    start_ms: int
    end_ms: int
    tag: str
    text: str

    @property
    def duration_ms(self) -> int:
        return max(200, self.end_ms - self.start_ms)


# =========================================================
# GENERIC HELPERS
# =========================================================
def secret_value(name: str, default: str = "") -> str:
    value = os.getenv(name, "")
    if value:
        return value.strip()
    try:
        raw = st.secrets.get(name, default)
        return str(raw).strip() if raw is not None else default
    except Exception:
        return default


def run_command(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "Command failed")[-4000:]
        raise RuntimeError(message)
    return result


def ffprobe_duration(path: Path) -> float:
    result = run_command(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        timeout=120,
    )
    return float(result.stdout.strip())


def ms_to_srt(ms: int) -> str:
    ms = max(0, int(ms))
    hours, remainder = divmod(ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def to_ms(h: str, m: str, s: str, ms: str) -> int:
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)


def strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:srt|text)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S).strip()


def atempo_chain(factor: float) -> str:
    factor = max(0.25, min(4.0, factor))
    parts: list[float] = []
    while factor > 2.0:
        parts.append(2.0)
        factor /= 2.0
    while factor < 0.5:
        parts.append(0.5)
        factor /= 0.5
    parts.append(factor)
    return ",".join(f"atempo={part:.6f}" for part in parts)


def split_srt_chunks(srt_text: str, max_chars: int = 8500) -> list[str]:
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    chunks: list[str] = []
    current: list[str] = []
    count = 0
    for block in blocks:
        size = len(block) + 2
        if current and count + size > max_chars:
            chunks.append("\n\n".join(current))
            current, count = [], 0
        current.append(block)
        count += size
    if current:
        chunks.append("\n\n".join(current))
    return chunks


# =========================================================
# AUTHENTICATION
# =========================================================
def init_session() -> None:
    defaults = {
        "logged_in": False,
        "session_token": "",
        "source_srt": "",
        "translated_srt": "",
        "dubbed_mp3": b"",
        "dubbed_mp4": b"",
        "source_name": "video",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def render_login() -> bool:
    username_expected = secret_value("APP_USERNAME", "owner")
    password_expected = secret_value("APP_PASSWORD") or secret_value("ADMIN_PASSWORD")

    st.markdown(
        '<div class="hero"><h1>AI KHEMRA BRO</h1><p>GLOBAL AI DUBBING & SUBTITLING WORKSTATION</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("## 🔐 Login")

    if not password_expected:
        st.error("APP_PASSWORD or ADMIN_PASSWORD is missing in Streamlit Secrets / Railway Variables.")
        return False

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", value=username_expected)
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        if secrets.compare_digest(username.strip(), username_expected) and secrets.compare_digest(password, password_expected):
            st.session_state.logged_in = True
            st.session_state.session_token = secrets.token_urlsafe(24)
            st.rerun()
        else:
            st.error("Username or password is incorrect.")
    return False


# =========================================================
# WHISPER / GEMINI
# =========================================================
@st.cache_resource(show_spinner=False)
def load_whisper_model(model_name: str):
    if WhisperModel is None:
        raise RuntimeError("faster-whisper is missing. Check requirements.txt")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    return WhisperModel(model_name, device="cpu", compute_type=compute_type)


def transcribe_video(video_path: Path, whisper_model: str) -> str:
    audio_path = video_path.with_suffix(".wav")
    run_command(
        [
            "ffmpeg", "-y", "-i", str(video_path), "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(audio_path),
        ],
        timeout=900,
    )

    model = load_whisper_model(whisper_model)
    segments, _info = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=True,
    )

    blocks: list[str] = []
    for index, segment in enumerate(segments, 1):
        text = re.sub(r"\s+", " ", segment.text).strip()
        if not text:
            continue
        start_ms = int(float(segment.start) * 1000)
        end_ms = max(start_ms + 300, int(float(segment.end) * 1000))
        blocks.append(f"{index}\n{ms_to_srt(start_ms)} --> {ms_to_srt(end_ms)}\n{text}")

    if not blocks:
        raise RuntimeError("No speech was detected in the uploaded video.")
    return "\n\n".join(blocks) + "\n"


def translate_and_classify_srt(
    source_srt: str,
    api_key: str,
    model_name: str,
    style: str,
) -> str:
    if genai is None:
        raise RuntimeError("google-genai is missing. Check requirements.txt")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing in Secrets / Variables.")

    style_instruction = {
        "Chinese Drama Pro": (
            "Use natural spoken Khmer for Chinese drama dubbing. Preserve relationships, titles, emotion, "
            "status, jokes, threats, affection and dramatic tone. Avoid literal translation."
        ),
        "100% Audio Sync": (
            "Use concise natural Khmer that can be spoken inside each original timestamp. Shorten wording "
            "without losing meaning or emotion."
        ),
        "Standard": "Use clear natural spoken Khmer and preserve the original meaning.",
    }[style]

    prompt = f"""You are a professional film dubbing translator and speaker classifier.
Translate the provided SRT into natural spoken Khmer.

Translation style:
{style_instruction}

For EVERY subtitle, add exactly one speaker tag at the start of the dialogue:
[BOY] child male
[GIRL] child female
[MAN] adult male
[WOMAN] adult female
[OLD_MAN] elderly male
[OLD_WOMAN] elderly female

Rules:
1. Keep subtitle numbers and timestamps exactly unchanged.
2. Return valid SRT only. No markdown and no explanation.
3. Do not skip any subtitle.
4. Use only Khmer dialogue after the speaker tag.
5. Infer age and gender from dialogue/context. When uncertain use [MAN] or [WOMAN].
6. Keep lines concise for dubbing and preserve emotion.

SRT:
"""

    client = genai.Client(api_key=api_key)
    translated: list[str] = []
    for chunk_number, chunk in enumerate(split_srt_chunks(source_srt), 1):
        response = client.models.generate_content(model=model_name, contents=prompt + chunk)
        text = strip_code_fences(response.text or "")
        if "-->" not in text:
            raise RuntimeError(f"Gemini returned an invalid result for part {chunk_number}.")
        translated.append(text)
    return "\n\n".join(translated).strip() + "\n"


# =========================================================
# SRT / TTS / VIDEO
# =========================================================
def parse_srt(srt_text: str, forced_voice_mode: str = "Auto") -> list[SubtitleItem]:
    items: list[SubtitleItem] = []
    for raw_block in re.split(r"\n\s*\n", srt_text.strip()):
        lines = [line.strip() for line in raw_block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        time_idx = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time_idx is None:
            continue
        match = TIME_PATTERN.search(lines[time_idx])
        if not match:
            continue

        index = int(lines[0]) if lines[0].isdigit() else len(items) + 1
        start_ms = to_ms(*match.groups()[:4])
        end_ms = to_ms(*match.groups()[4:])
        dialogue = " ".join(lines[time_idx + 1:]).strip()

        tag = "MAN"
        tag_match = TAG_PATTERN.match(dialogue)
        if tag_match:
            tag = tag_match.group(1).upper()
            dialogue = dialogue[tag_match.end():].strip()

        if forced_voice_mode == "All Male":
            tag = "MAN"
        elif forced_voice_mode == "All Female":
            tag = "WOMAN"

        if dialogue:
            items.append(SubtitleItem(index, start_ms, end_ms, tag, dialogue))

    if not items:
        raise RuntimeError("No valid subtitle blocks were found.")
    return items


async def synthesize_one(item: SubtitleItem, output_path: Path) -> None:
    profile = VOICE_PROFILES.get(item.tag, VOICE_PROFILES["MAN"])
    communicate = edge_tts.Communicate(
        text=item.text,
        voice=profile["voice"],
        rate=profile["rate"],
        pitch=profile["pitch"],
        volume="+0%",
    )
    await communicate.save(str(output_path))


def run_async(coro) -> None:
    try:
        asyncio.run(coro)
    except RuntimeError as exc:
        if "asyncio.run() cannot be called" not in str(exc):
            raise
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()


def create_dubbed_audio(
    items: list[SubtitleItem],
    video_duration_s: float,
    workdir: Path,
    sync_mode: str,
    progress_callback=None,
) -> Path:
    prepared_paths: list[Path] = []

    for idx, item in enumerate(items):
        raw_path = workdir / f"tts_{idx:04d}.mp3"
        fitted_path = workdir / f"fit_{idx:04d}.wav"
        run_async(synthesize_one(item, raw_path))

        raw_duration = max(0.05, ffprobe_duration(raw_path))
        target_duration = max(0.20, item.duration_ms / 1000.0)
        tempo_factor = raw_duration / target_duration

        if sync_mode == "Speed Up Only" and tempo_factor < 1.0:
            # Keep natural speech if already shorter than the subtitle window.
            tempo_filter = "anull"
        else:
            tempo_filter = atempo_chain(tempo_factor)

        run_command(
            [
                "ffmpeg", "-y", "-i", str(raw_path),
                "-af", f"{tempo_filter},apad,atrim=0:{target_duration:.3f}",
                "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(fitted_path),
            ],
            timeout=240,
        )
        prepared_paths.append(fitted_path)
        if progress_callback:
            progress_callback((idx + 1) / max(1, len(items)))

    output_path = workdir / "dubbed_audio.mp3"
    command = ["ffmpeg", "-y"]
    for path in prepared_paths:
        command += ["-i", str(path)]

    filter_parts: list[str] = []
    mix_labels: list[str] = []
    for idx, item in enumerate(items):
        label = f"a{idx}"
        filter_parts.append(f"[{idx}:a]adelay={item.start_ms}|{item.start_ms}[{label}]")
        mix_labels.append(f"[{label}]")

    filter_parts.append(
        f"{''.join(mix_labels)}amix=inputs={len(items)}:normalize=0:dropout_transition=0,"
        f"apad,atrim=0:{video_duration_s:.3f}[mix]"
    )
    command += [
        "-filter_complex", ";".join(filter_parts),
        "-map", "[mix]", "-ar", "44100", "-ac", "2", "-b:a", "192k", str(output_path),
    ]
    run_command(command, timeout=1800)
    return output_path


def merge_video_audio(video_path: Path, audio_path: Path, output_path: Path) -> None:
    run_command(
        [
            "ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_path),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
            "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(output_path),
        ],
        timeout=1800,
    )


# =========================================================
# UI
# =========================================================
def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("## 👤 Account")
        st.write(f"**{secret_value('APP_USERNAME', 'owner')}**")
        role = secret_value("APP_ROLE", "OWNER")
        expiry = secret_value("PLAN_EXPIRY", "")
        st.caption(f"ROLE: {role}")
        if expiry:
            try:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                days = max(0, (expiry_date - date.today()).days)
                st.caption(f"PLAN: {expiry} · {days} DAYS LEFT")
            except ValueError:
                st.caption(f"PLAN: {expiry}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.session_token = ""
            st.rerun()

        st.divider()
        st.markdown("## 🎭 Translation Style")
        style = st.radio(
            "Translation style",
            ["Chinese Drama Pro", "100% Audio Sync", "Standard"],
            label_visibility="collapsed",
        )

        st.markdown("## ⚙️ Audio Sync Mode")
        sync_mode = st.radio(
            "Audio sync",
            ["Speed Up Only", "Speed Up & Slow Down"],
            label_visibility="collapsed",
        )

        st.markdown("## 🗣️ Voice Mode")
        voice_mode = st.radio(
            "Voice mode",
            ["Auto", "All Male", "All Female"],
            label_visibility="collapsed",
        )
        st.caption("Auto supports boy, girl, adult male/female and elderly male/female.")

        st.markdown("## 🧠 AI Model")
        gemini_model = st.selectbox(
            "Gemini model",
            [DEFAULT_GEMINI_MODEL, "gemini-2.5-flash-lite"],
        )
        whisper_model = st.selectbox(
            "Whisper model",
            [DEFAULT_WHISPER_MODEL, "base", "small", "medium"],
        )

    return {
        "style": style,
        "sync_mode": sync_mode,
        "voice_mode": voice_mode,
        "gemini_model": gemini_model,
        "whisper_model": whisper_model,
    }


def clear_project() -> None:
    for key in ["source_srt", "translated_srt", "dubbed_mp3", "dubbed_mp4", "source_name"]:
        st.session_state[key] = "" if key.endswith("srt") or key == "source_name" else b""
    st.rerun()


def main() -> None:
    init_session()
    if not st.session_state.logged_in:
        render_login()
        return

    settings = render_sidebar()
    gemini_key = secret_value("GEMINI_API_KEY")

    st.markdown(
        '<div class="hero"><h1>AI KHEMRA BRO</h1><p>VIDEO → KHMER SRT → 6 VOICES → MP3 → MP4</p></div>',
        unsafe_allow_html=True,
    )

    if gemini_key:
        st.markdown('<div class="ok">✅ Gemini API is connected securely from the server.</div>', unsafe_allow_html=True)
    else:
        st.error("GEMINI_API_KEY is missing in Streamlit Secrets / Railway Variables.")

    uploaded = st.file_uploader(
        f"📤 Upload Video — maximum {MAX_FILE_MB} MB",
        type=["mp4", "mov", "mkv", "avi", "webm"],
    )

    if uploaded is not None:
        file_size_mb = len(uploaded.getvalue()) / (1024 * 1024)
        if file_size_mb > MAX_FILE_MB:
            st.error(f"Video is {file_size_mb:.1f} MB. Maximum is {MAX_FILE_MB} MB.")
            uploaded = None
        else:
            st.markdown(
                f'<div class="card">✅ <b>{uploaded.name}</b><br><span class="small">{file_size_mb:.1f} MB</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("## 1️⃣ Generate Khmer Subtitles")
    generate_disabled = uploaded is None or not gemini_key
    if st.button("🚀 Generate Subtitles & Translate", use_container_width=True, disabled=generate_disabled):
        video_bytes = uploaded.getvalue()
        suffix = Path(uploaded.name).suffix or ".mp4"
        with tempfile.TemporaryDirectory() as temp_dir:
            workdir = Path(temp_dir)
            video_path = workdir / f"input{suffix}"
            video_path.write_bytes(video_bytes)
            duration = ffprobe_duration(video_path)
            if duration > MAX_VIDEO_MINUTES * 60:
                st.error(f"Video is longer than {MAX_VIDEO_MINUTES} minutes.")
                st.stop()

            status = st.status("Processing video…", expanded=True)
            try:
                status.write("🎧 Extracting and transcribing audio with Whisper…")
                source_srt = transcribe_video(video_path, settings["whisper_model"])
                status.write("🌐 Translating to Khmer and detecting six voice types…")
                translated_srt = translate_and_classify_srt(
                    source_srt,
                    gemini_key,
                    settings["gemini_model"],
                    settings["style"],
                )
                st.session_state.source_srt = source_srt
                st.session_state.translated_srt = translated_srt
                st.session_state.source_name = Path(uploaded.name).stem
                st.session_state.video_bytes = video_bytes
                status.update(label="SRT generation complete", state="complete")
            except Exception as exc:
                status.update(label="Processing failed", state="error")
                st.error(str(exc))

    if st.session_state.translated_srt:
        edited_srt = st.text_area(
            "Generated Khmer SRT — you can edit before creating voice",
            value=st.session_state.translated_srt,
            height=420,
        )
        st.session_state.translated_srt = edited_srt
        st.download_button(
            "⬇️ Download Khmer SRT",
            data=edited_srt.encode("utf-8"),
            file_name=f"{st.session_state.source_name}_khmer.srt",
            mime="application/x-subrip",
            use_container_width=True,
        )

    st.markdown("## 2️⃣ Generate Six-Voice Dubbed Audio")
    tts_disabled = not st.session_state.translated_srt or not st.session_state.get("video_bytes")
    if st.button("🎙️ Generate Dubbed MP3 + MP4", use_container_width=True, disabled=tts_disabled):
        suffix = ".mp4"
        with tempfile.TemporaryDirectory() as temp_dir:
            workdir = Path(temp_dir)
            video_path = workdir / f"source{suffix}"
            video_path.write_bytes(st.session_state.video_bytes)
            video_duration = ffprobe_duration(video_path)
            output_video = workdir / "dubbed_video.mp4"
            progress = st.progress(0, text="Generating character voices…")
            try:
                items = parse_srt(st.session_state.translated_srt, settings["voice_mode"])
                audio_path = create_dubbed_audio(
                    items,
                    video_duration,
                    workdir,
                    settings["sync_mode"],
                    progress_callback=lambda value: progress.progress(value, text="Generating and syncing voices…"),
                )
                progress.progress(1.0, text="Merging Khmer audio with video…")
                merge_video_audio(video_path, audio_path, output_video)
                st.session_state.dubbed_mp3 = audio_path.read_bytes()
                st.session_state.dubbed_mp4 = output_video.read_bytes()
                progress.empty()
                st.success("Dubbed audio and translated video are ready.")
            except Exception as exc:
                progress.empty()
                st.error(str(exc))

    if st.session_state.dubbed_mp3:
        st.audio(st.session_state.dubbed_mp3, format="audio/mp3")
        st.download_button(
            "⬇️ Download Dubbed MP3",
            data=st.session_state.dubbed_mp3,
            file_name=f"{st.session_state.source_name}_khmer.mp3",
            mime="audio/mpeg",
            use_container_width=True,
        )

    if st.session_state.dubbed_mp4:
        st.video(st.session_state.dubbed_mp4)
        st.download_button(
            "⬇️ Download Translated MP4",
            data=st.session_state.dubbed_mp4,
            file_name=f"{st.session_state.source_name}_khmer_dubbed.mp4",
            mime="video/mp4",
            use_container_width=True,
        )

    st.divider()
    if st.button("🗑️ Clear Video Project", use_container_width=True):
        clear_project()


if __name__ == "__main__":
    main()
