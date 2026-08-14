import ast
import re
from pathlib import Path

root = Path(__file__).parent
app_path = root / "app.py"
source = app_path.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(app_path))
needed = {"normalize_dialogue", "prepare_tts_text", "parse_srt"}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in needed]
namespace = {"re": re}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(app_path), "exec"), namespace)

prepare_tts_text = namespace["prepare_tts_text"]
parse_srt = namespace["parse_srt"]

# A user-written (...) or ... becomes one intentional, natural pause marker.
assert prepare_tts_text("ចាំសិន (...) ខ្ញុំគិតមើល") == "ចាំសិន … ខ្ញុំគិតមើល។"
assert prepare_tts_text("កុំប្រញាប់...យើងនិយាយគ្នាសិន") == "កុំប្រញាប់ … យើងនិយាយគ្នាសិន។"
assert prepare_tts_text("ខ្ញុំយល់ហើយ……") == "ខ្ញុំយល់ហើយ …"

# The published example must contain rapid, ordered speaker turns and all canonical tags.
fixture = (root / "SRT_MULTICHARACTER_THOUGHTS_NATURAL_KH.srt").read_text(encoding="utf-8")
cues = parse_srt(fixture)
assert len(cues) == 18
assert {cue["tag"] for cue in cues} == {"M", "F", "M_THINK", "F_THINK"}
assert sum(cue["tag"] == "M_THINK" for cue in cues) >= 3
assert sum(cue["tag"] == "F_THINK" for cue in cues) >= 3
assert all(cues[index]["start"] < cues[index + 1]["start"] for index in range(len(cues) - 1))
assert all(cues[index + 1]["start"] - cues[index]["end"] <= 200 for index in range(len(cues) - 1))

# Thought voices stay clear and intimate; default echo is intentionally absent.
assert "Use one ellipsis (…) only" in source
assert "'volume=0.92'" in source
assert "aecho=" not in source
print("v6.6.1 prompt rhythm and multi-character SRT example tests: OK")
