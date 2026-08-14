import ast
import subprocess
from pathlib import Path

source_path = Path(__file__).with_name("app.py")
source = source_path.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(source_path))
assignments = {"VOICE_FADE_IN_SECONDS", "VOICE_FADE_OUT_SECONDS", "MIN_VOICE_GAP_MS", "MAX_TEMPO_SPEED", "FINAL_LEVELER_FILTER"}
functions = {"atempo_chain"}
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in assignments for name in names):
            nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in functions:
        nodes.append(node)
namespace = {}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

# Timing changes avoid staccato dips, forced rushing, and clipped final words.
assert namespace["VOICE_FADE_IN_SECONDS"] == 0.010
assert namespace["VOICE_FADE_OUT_SECONDS"] == 0.018
assert namespace["MIN_VOICE_GAP_MS"] == 0
assert namespace["MAX_TEMPO_SPEED"] == 1.00
assert namespace["FINAL_LEVELER_FILTER"] == "dynaudnorm=f=1600:g=3:p=0.96:m=1.12:n=1:c=1:b=1:o=0.92"
assert namespace["atempo_chain"](1.00) == ""

# Confirm the light master chain preserves a natural voice rather than pumping it.
assert "highpass=f=75:p=2" in source
assert "lowpass=f=7600:p=2" in source
assert "loudnorm=I=-18:TP=-2.0:LRA=8" in source
assert "trim_seconds = audio_seconds" in source
assert "previous_voice_end_ms - 24" in source
assert "ratio=1.28:attack=60:release=400" not in source
assert "FINAL_LEVELER_FILTER" in source
assert "aecho=" not in source

# Confirm distinct action identities and four animated microphones are in the UI.
assert ".st-key-translate_btn button::before" in source
assert "content:'🧠'" in source
assert "@keyframes micFloat" in source
assert source.count('class="voice-mic"') >= 12

# Ask FFmpeg to parse the exact audio filters that need to be valid at runtime.
filters = (
    "highpass=f=75:p=2,lowpass=f=7600:p=2,"
    "equalizer=f=4300:t=q:w=1.0:g=-1.2,"
    "equalizer=f=6200:t=q:w=0.9:g=-1.8,"
    "dynaudnorm=f=1600:g=3:p=0.96:m=1.12:n=1:c=1:b=1:o=0.92,"
    "afade=t=in:st=0:d=0.010,afade=t=out:st=0.8:d=0.018,"
    "alimiter=limit=0.95:attack=30:release=520"
)
result = subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-af", filters, "-f", "null", "-"],
    capture_output=True, text=True, timeout=30,
)
assert result.returncode == 0, result.stderr
print("v6.6.1 natural no-cut audio and UI animation tests: OK")
