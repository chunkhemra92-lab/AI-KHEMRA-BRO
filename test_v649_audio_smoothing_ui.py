import ast
import subprocess
from pathlib import Path

source_path = Path(__file__).with_name("app.py")
source = source_path.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(source_path))
assignments = {"VOICE_FADE_IN_SECONDS", "VOICE_FADE_OUT_SECONDS", "MIN_VOICE_GAP_MS", "MAX_TEMPO_SPEED"}
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

# Timing changes avoid staccato dips and forced rushing.
assert namespace["VOICE_FADE_IN_SECONDS"] == 0.018
assert namespace["VOICE_FADE_OUT_SECONDS"] == 0.030
assert namespace["MIN_VOICE_GAP_MS"] == 0
assert namespace["MAX_TEMPO_SPEED"] == 1.10
assert namespace["atempo_chain"](1.10) == "atempo=1.10000"

# Confirm the new slow, low-ratio mastering configuration is present.
assert "ratio=1.28:attack=60:release=400" in source
assert "ratio=1.18:attack=90:release=520" in source
assert "loudnorm=I=-17:TP=-2.0:LRA=7" in source
assert "aecho=" not in source

# Confirm distinct action identities and four animated microphones are in the UI.
assert ".st-key-translate_btn button::before" in source
assert "content:'🧠'" in source
assert "@keyframes micFloat" in source
assert source.count('class="voice-mic"') >= 12

# Ask FFmpeg to parse the exact audio filters that need to be valid at runtime.
filters = (
    "highpass=f=85:p=2,lowpass=f=7000:p=2,"
    "acompressor=threshold=-18dB:ratio=1.28:attack=60:release=400:makeup=1.00:knee=6,"
    "afade=t=in:st=0:d=0.018,afade=t=out:st=0.8:d=0.030,"
    "alimiter=limit=0.94:attack=20:release=260"
)
result = subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-af", filters, "-f", "null", "-"],
    capture_output=True, text=True, timeout=30,
)
assert result.returncode == 0, result.stderr
print("v6.4.9 audio smoothing and UI animation tests: OK")
