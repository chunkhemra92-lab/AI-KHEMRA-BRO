import ast
import re
from pathlib import Path

source_path = Path(__file__).with_name("app.py")
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
needed_assignments = {"TAG_ALIASES", "NON_KHMER_SCRIPT_RE", "KHMER_DUBBING_RULES"}
needed_functions = {
    "normalize_voice_tag",
    "contains_non_khmer_script",
    "build_multilingual_translation_prompt",
    "normalize_dialogue",
    "seconds_to_srt",
    "build_srt",
}
nodes = []
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        names = []
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
        elif isinstance(node.target, ast.Name):
            names.append(node.target.id)
        if any(name in needed_assignments for name in names):
            nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in needed_functions:
        nodes.append(node)

namespace = {"re": re}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

contains_non_khmer_script = namespace["contains_non_khmer_script"]
normalize_voice_tag = namespace["normalize_voice_tag"]
build_multilingual_translation_prompt = namespace["build_multilingual_translation_prompt"]
build_srt = namespace["build_srt"]

assert contains_non_khmer_script("សួស្តី") is False
for foreign_text in ("Hello", "你好", "안녕하세요", "สวัสดี", "xin chào", "đ"):
    assert contains_non_khmer_script(foreign_text) is True, foreign_text

assert normalize_voice_tag("M_ADULT") == "M"
assert normalize_voice_tag("F_OLD") == "F"
assert normalize_voice_tag("M_THINK") == "M_THINK"
assert normalize_voice_tag("unknown") == "M"

prompt = build_multilingual_translation_prompt("ID=1 | SOURCE=Hello", "English")
for required_phrase in ("RULE 1", "RULE 2", "RULE 3", "RULE 4", "RULE 5", "RULE 6", "Khmer script only"):
    assert required_phrase in prompt, required_phrase

cues = [{"id": 1, "start": 0.0, "end": 1.5}]
valid_srt = build_srt(cues, {1: {"tag": "M_ADULT", "text": "សួស្តីបង"}})
assert "[M] សួស្តីបង" in valid_srt

try:
    build_srt(cues, {1: {"tag": "F", "text": "Hello"}})
except RuntimeError:
    pass
else:
    raise AssertionError("Non-Khmer output was not rejected")

print("v6.4 translation-rule and SRT validation tests: OK")
