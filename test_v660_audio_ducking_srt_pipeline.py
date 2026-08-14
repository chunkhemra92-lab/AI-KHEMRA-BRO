import ast
import asyncio
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import edge_tts

root = Path(__file__).parent
source_path = root / "app.py"
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
assignments = {
    "PISITH", "SREYMOM", "VOICE_PROFILES", "VOICE_FADE_IN_SECONDS",
    "VOICE_FADE_OUT_SECONDS", "MIN_VOICE_GAP_MS", "MAX_TEMPO_SPEED",
    "FINAL_LEVELER_FILTER", "TAG_ALIASES", "NON_KHMER_SCRIPT_RE", "DUCKING_DEFAULTS",
}
functions = {
    "normalize_voice_tag", "contains_non_khmer_script", "normalize_dialogue",
    "prepare_tts_text", "synthesize", "run_async", "character_voice_filters",
    "voice_tone_filters", "normalized_ducking_config", "append_audio_master_filters",
    "probe_audio_duration", "atempo_chain", "parse_srt", "create_mp3",
}
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in assignments for name in names):
            nodes.append(node)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in functions:
        nodes.append(node)

namespace = {
    "re": re, "asyncio": asyncio, "edge_tts": edge_tts, "subprocess": subprocess,
    "tempfile": tempfile, "Path": Path, "ThreadPoolExecutor": ThreadPoolExecutor,
    "as_completed": as_completed,
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

srt = """1
00:00:00,000 --> 00:00:02,400
[M] អូនកុំបារម្ភអីណា បងនៅទីនេះ។

2
00:00:02,550 --> 00:00:05,000
[F_THINK] សង្ឃឹមថាអ្វីៗនឹងប្រសើរឡើង។
"""

with tempfile.TemporaryDirectory() as temp_dir:
    music = Path(temp_dir) / "music.mp3"
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
            "-i", "sine=frequency=140:sample_rate=48000:duration=1.2",
            "-c:a", "libmp3lame", "-b:a", "128k", str(music),
        ],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr

    ducked = namespace["create_mp3"](
        srt, background_music_path=music,
        ducking_config={"enabled": True, "music_gain": 0.42, "ratio": 8, "release_ms": 700},
    )
    plain = namespace["create_mp3"](srt)
    assert len(ducked) > 2000
    assert len(plain) > 2000

print("v6.6.0 SRT pipeline Audio Ducking and no-music fallback: OK")
