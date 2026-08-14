import ast
import asyncio
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import edge_tts

source_path = Path(__file__).with_name("app.py")
source = source_path.read_text(encoding="utf-8")
assert "MAX_TEMPO_SPEED = 1.00" in source
assert "trim_seconds = audio_seconds" in source
assert "render_start_ms = start_ms if index == 0 else max(start_ms, previous_voice_end_ms - 24)" in source
assert "safe_speed = min(max(1.0, required_speed), MAX_TEMPO_SPEED)" not in source
assert "coalesce_continuation_cues(cues)" in source
assert "CONTINUATION_GAP_MS = 260" in source
assert "acompressor=threshold=-18dB:ratio=1.28" not in source

tree = ast.parse(source, filename=str(source_path))
assignments = {
    "PISITH", "SREYMOM", "VOICE_PROFILES", "VOICE_FADE_IN_SECONDS",
    "VOICE_FADE_OUT_SECONDS", "MIN_VOICE_GAP_MS", "CONTINUATION_GAP_MS", "MAX_TEMPO_SPEED",
    "FINAL_LEVELER_FILTER", "TAG_ALIASES", "NON_KHMER_SCRIPT_RE", "DUCKING_DEFAULTS",
}
functions = {
    "normalize_voice_tag", "contains_non_khmer_script", "normalize_dialogue",
    "prepare_tts_text", "synthesize", "run_async", "character_voice_filters",
    "voice_tone_filters", "normalized_ducking_config", "append_audio_master_filters",
    "probe_audio_duration", "atempo_chain", "parse_srt", "coalesce_continuation_cues", "create_mp3",
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

# These deliberately short SRT slots are long enough to be readable on screen but
# shorter than natural Khmer Edge speech. The output must preserve both full phrases.
srt = """1
00:00:00,000 --> 00:00:01,150
[M] បងមកដល់ហើយ អូនកុំបារម្ភអីណា។

2
00:00:01,200 --> 00:00:02,350
[F] ពិតមែនឬ ខ្ញុំរង់ចាំបងយូរហើយ។
"""
output = namespace["create_mp3"](srt)
with tempfile.TemporaryDirectory() as temp_dir:
    path = Path(temp_dir) / "natural_no_cut.mp3"
    path.write_bytes(output)
    duration = namespace["probe_audio_duration"](path)

# Old forced-slot behavior ended around 2.7 sec. Preserving both natural phrases
# must yield a clearly longer file without truncating their final words.
assert duration > 5.0, duration
print(f"v6.6.1 natural no-cut Khmer speech: OK ({duration:.2f} sec)")
