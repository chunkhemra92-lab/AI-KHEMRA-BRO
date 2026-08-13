import ast
import re
import subprocess
import tempfile
from pathlib import Path

source_path = Path(__file__).with_name("app.py")
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
needed_assignments = {"PISITH", "SREYMOM", "VOICE_PROFILES", "TAG_ALIASES", "KHMER_DUBBING_RULES"}
needed_functions = {"character_voice_filters", "_clean_api_keys", "load_secret_gemini_api_keys", "normalize_voice_tag"}
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in needed_assignments for name in names):
            nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in needed_functions:
        nodes.append(node)

class FakeSecrets(dict):
    def get(self, key, default=None):
        return super().get(key, default)

class FakeStreamlit:
    def __init__(self):
        self.secrets = FakeSecrets({"GEMINI_API_KEYS": "secret-one, secret-two\nsecret-one"})

namespace = {"re": re, "st": FakeStreamlit()}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

profiles = namespace["VOICE_PROFILES"]
assert profiles["M_THINK"]["rate"] == "-13%"
assert profiles["F_THINK"]["volume"] == "-5%"
assert profiles["M"]["volume"] == "+2%"
assert namespace["normalize_voice_tag"]("M_ADULT") == "M"
assert namespace["normalize_voice_tag"]("F_THINK") == "F_THINK"

think_filters = namespace["character_voice_filters"]("M_THINK")
normal_filters = namespace["character_voice_filters"]("M")
assert any(item.startswith("aecho=") for item in think_filters)
assert any(item == "volume=0.78" for item in think_filters)
assert not any(item.startswith("aecho=") for item in normal_filters)
assert namespace["load_secret_gemini_api_keys"]() == "secret-one\nsecret-two"

rules = namespace["KHMER_DUBBING_RULES"]
for marker in ("RULE 1", "RULE 2", "RULE 3", "RULE 4", "RULE 5", "RULE 6", "FACEBOOK-SAFE", "word-for-word"):
    assert marker in rules

# Validate the distinctive thought-voice FFmpeg filter chain using an artificial sine input.
with tempfile.TemporaryDirectory() as temp_dir:
    output = Path(temp_dir) / "thought.wav"
    filter_chain = ",".join([
        "highpass=f=85:p=2", "lowpass=f=7000:p=2", *think_filters,
        "acompressor=threshold=-23dB:ratio=2.0:attack=14:release=190:makeup=1.15:knee=4",
    ])
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
        "-t", "0.4", "-af", filter_chain, str(output),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    assert output.exists() and output.stat().st_size > 1000

print("Voice profiles, Facebook-safe six rules, Secrets fallback, and thought-audio filters: OK")
