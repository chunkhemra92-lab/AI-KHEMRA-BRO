"""End-to-end reliability and performance test for AI KHEMRA BRO v6.2.

This test extracts only the production audio helpers from app.py, then runs the real
Edge TTS service, FFmpeg mix path, and faster-whisper base model without executing
the Streamlit user interface.  It writes machine-readable metrics to
v6_2_audio_metrics.json for release reporting.
"""

import ast
import asyncio
import json
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import edge_tts
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

REQUIRED_FUNCTIONS = {
    "_voice_tag_key",
    "compact_voice_tag",
    "is_known_voice_tag",
    "lock_voice_tag",
    "normalize_dialogue",
    "prepare_tts_text",
    "synthesize",
    "probe_audio_duration",
    "atempo_chain",
    "effective_voice_tag",
    "character_voice_filters",
    "contains_cjk",
    "convert_tts_clip_to_pcm",
    "parse_srt",
    "run_async",
    "create_mp3",
}

PISITH = "km-KH-PisethNeural"
SREYMOM = "km-KH-SreymomNeural"
VOICE_PROFILES = {
    "M_ADULT": {"voice": PISITH, "rate": "-1%", "pitch": "+0Hz", "volume": "+2%"},
    "F_ADULT": {"voice": SREYMOM, "rate": "-1%", "pitch": "+0Hz", "volume": "+2%"},
    "M_THINK": {"voice": PISITH, "rate": "-4%", "pitch": "-2Hz", "volume": "+0%"},
    "F_THINK": {"voice": SREYMOM, "rate": "-4%", "pitch": "-1Hz", "volume": "+0%"},
}
LOCKED_VOICE_PROFILES = {
    "M": VOICE_PROFILES["M_ADULT"],
    "F": VOICE_PROFILES["F_ADULT"],
    "M_THINK": VOICE_PROFILES["M_THINK"],
    "F_THINK": VOICE_PROFILES["F_THINK"],
}

namespace = {
    "asyncio": asyncio,
    "as_completed": as_completed,
    "contains_cjk": None,
    "DEFAULT_TARGET_LANGUAGE": "Khmer",
    "EDGE_TTS_MAX_CONCURRENT_REQUESTS": 2,
    "EDGE_TTS_REQUEST_TIMEOUT_SECONDS": 75,
    "edge_tts": edge_tts,
    "FFMPEG_CLIP_CONVERSION_TIMEOUT_SECONDS": 180,
    "FFMPEG_FINAL_MIX_TIMEOUT_SECONDS": 900,
    "MAX_TEMPO_SPEED": 1.65,
    "Path": Path,
    "PISITH": PISITH,
    "re": re,
    "SREYMOM": SREYMOM,
    "subprocess": subprocess,
    "tempfile": tempfile,
    "ThreadPoolExecutor": ThreadPoolExecutor,
    "VOICE_FADE_IN_SECONDS": 0.045,
    "VOICE_FADE_OUT_SECONDS": 0.070,
    "LOCKED_VOICE_TAGS": frozenset({"M", "F", "M_THINK", "F_THINK"}),
    "LOCKED_VOICE_PROFILES": LOCKED_VOICE_PROFILES,
    "VOICE_PROFILES": VOICE_PROFILES,
}
selected_nodes = [
    node for node in TREE.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in REQUIRED_FUNCTIONS
]
exec(compile(ast.Module(body=selected_nodes, type_ignores=[]), "app.py", "exec"), namespace)
namespace["target_language_details"] = lambda _value: {"code": "km"}


def ffprobe_channels(path: Path) -> int:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=channels", "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return int(result.stdout.strip())


def main() -> None:
    metrics = {"test": "AI KHEMRA BRO v6.2 audio integration", "voices": {}}
    synthesis = namespace["synthesize"]
    probe_audio_duration = namespace["probe_audio_duration"]
    create_mp3 = namespace["create_mp3"]

    with tempfile.TemporaryDirectory(prefix="khbr-v62-audio-") as folder:
        root = Path(folder)
        reference_mp3 = root / "male_reference.mp3"
        phrase = "សួស្តី។ នេះជាការសាកល្បងសំឡេងខ្មែរសម្រាប់ AI KHEMRA BRO។"

        for label, profile_key, output in (
            ("M", "M_ADULT", reference_mp3),
            ("F", "F_ADULT", root / "female_reference.mp3"),
        ):
            started = time.perf_counter()
            asyncio.run(synthesis(phrase, VOICE_PROFILES[profile_key], output))
            elapsed = time.perf_counter() - started
            duration = probe_audio_duration(output)
            assert output.exists() and output.stat().st_size > 500, f"{label} voice output is missing or too small"
            assert duration > 0.25, f"{label} voice duration is invalid"
            metrics["voices"][label] = {
                "bytes": output.stat().st_size,
                "duration_seconds": round(duration, 3),
                "synthesis_seconds": round(elapsed, 3),
                "realtime_factor": round(elapsed / duration, 3),
            }

        overlap_srt = """1
00:00:00,000 --> 00:00:02,800
[M] សួស្តី ខ្ញុំកំពុងសាកល្បងសំឡេងប្រុស។

2
00:00:01,300 --> 00:00:04,200
[F] ខ្ញុំកំពុងសាកល្បងសំឡេងស្រីផងដែរ។

3
00:00:04,500 --> 00:00:06,800
[M_THINK] ខ្ញុំកំពុងគិតក្នុងចិត្ត។

4
00:00:05,400 --> 00:00:08,000
[F_THINK] ខ្ញុំក៏គិតក្នុងចិត្តដែរ។"""
        started = time.perf_counter()
        mixed_audio = create_mp3(overlap_srt, target_language="Khmer")
        mix_elapsed = time.perf_counter() - started
        mixed_path = root / "overlap_no_music.mp3"
        mixed_path.write_bytes(mixed_audio)
        mixed_duration = probe_audio_duration(mixed_path)
        assert len(mixed_audio) > 1000, "No-music mix output is unexpectedly small"
        assert mixed_duration >= 8.25, "Four-role overlap mix did not preserve the final SRT cue window"
        assert ffprobe_channels(mixed_path) == 2, "Final mix must remain stereo"
        metrics["four_role_no_music_overlap_mix"] = {
            "bytes": len(mixed_audio),
            "duration_seconds": round(mixed_duration, 3),
            "generation_seconds": round(mix_elapsed, 3),
            "stereo_channels": 2,
        }

        started = time.perf_counter()
        model = WhisperModel("base", device="cpu", compute_type="int8")
        metrics["faster_whisper_model_load_seconds"] = round(time.perf_counter() - started, 3)
        started = time.perf_counter()
        segments, _info = model.transcribe(
            str(reference_mp3),
            language="km",
            beam_size=3,
            best_of=2,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 220,
                "min_speech_duration_ms": 45,
                "speech_pad_ms": 380,
            },
            condition_on_previous_text=True,
            word_timestamps=True,
            no_speech_threshold=0.65,
            log_prob_threshold=-1.5,
            compression_ratio_threshold=2.6,
        )
        transcribed_segments = list(segments)
        transcription_elapsed = time.perf_counter() - started
        audio_duration = probe_audio_duration(reference_mp3)
        transcript = " ".join((segment.text or "").strip() for segment in transcribed_segments).strip()
        assert transcribed_segments, "faster-whisper produced no segments for a valid Khmer Edge TTS sample"
        metrics["faster_whisper_transcription"] = {
            "audio_seconds": round(audio_duration, 3),
            "transcription_seconds": round(transcription_elapsed, 3),
            "realtime_factor": round(transcription_elapsed / audio_duration, 3),
            "segment_count": len(transcribed_segments),
            "nonempty_transcript": bool(transcript),
        }

    metric_path = ROOT / "v6_2_audio_metrics.json"
    metric_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"v6.2 audio integration test passed; metrics: {metric_path}")


if __name__ == "__main__":
    main()
