import ast
import re
from pathlib import Path

app_path = Path(__file__).with_name("app.py")
source = app_path.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(app_path))
assignments = {"CONTINUATION_GAP_MS", "TAG_ALIASES"}
functions = {"normalize_voice_tag", "parse_srt", "coalesce_continuation_cues", "normalize_dialogue", "prepare_tts_text"}
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in assignments for name in names):
            nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in functions:
        nodes.append(node)
namespace = {"re": re}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(app_path), "exec"), namespace)

assert namespace["CONTINUATION_GAP_MS"] == 260
srt = """1
00:00:00,000 --> 00:00:01,400
[M] ខ្ញុំចង់ប្រាប់អូនរឿងមួយ។

2
00:00:01,470 --> 00:00:02,900
[M] តែអូនសន្យាថាកុំខឹងបងណា។

3
00:00:03,450 --> 00:00:04,900
[F] បងនិយាយមក ខ្ញុំកំពុងស្តាប់។

4
00:00:04,980 --> 00:00:06,200
[F] តែសូមកុំលាក់ការពិតពីខ្ញុំ។
"""
cues = namespace["parse_srt"](srt)
for cue in cues:
    cue["tag"] = namespace["normalize_voice_tag"](cue["tag"])
joined = namespace["coalesce_continuation_cues"](cues)

# The two close M fragments become one connected TTS phrase; the two F fragments
# do the same. A deliberate 550 ms turn-change remains a separate speaker turn.
assert len(joined) == 2
assert joined[0]["tag"] == "M"
assert joined[0]["text"] == "ខ្ញុំចង់ប្រាប់អូនរឿងមួយ តែអូនសន្យាថាកុំខឹងបងណា។"
assert joined[1]["tag"] == "F"
assert joined[1]["text"] == "បងនិយាយមក ខ្ញុំកំពុងស្តាប់ តែសូមកុំលាក់ការពិតពីខ្ញុំ។"
assert namespace["prepare_tts_text"](joined[0]["text"]).endswith("។")
assert "coalesce_continuation_cues(cues)" in source
print("v6.6.2 Khmer continuous-rhythm grouping: OK")
