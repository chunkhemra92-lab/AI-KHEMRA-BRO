"""Functional regression tests for v6.2 subtitle timing and tempo rules."""

import ast
import re
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path("app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
REQUIRED = {"_standardize_whisper_segments", "atempo_chain", "_voice_tag_key", "compact_voice_tag", "is_known_voice_tag", "lock_voice_tag", "parse_srt"}
NODES = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in REQUIRED]
namespace = {"re": re, "LOCKED_VOICE_TAGS": frozenset({"M", "F", "M_THINK", "F_THINK"})}
exec(compile(ast.Module(body=NODES, type_ignores=[]), "app.py", "exec"), namespace)


def segment(start, end, word):
    return SimpleNamespace(
        start=start,
        end=end,
        text=word,
        words=[SimpleNamespace(start=start, end=end, word=word)],
    )


def main():
    normalize = namespace["_standardize_whisper_segments"]
    cues = normalize([
        segment(0.0, 2.0, "ទីមួយ"),
        segment(1.3, 3.0, "ទីពីរ"),
    ])
    assert len(cues) == 2
    assert cues[1]["start"] == 1.3, "a meaningful original overlap must be preserved"

    tiny_overlap = normalize([
        segment(0.0, 1.0, "A"),
        segment(0.94, 2.0, "B"),
    ])
    assert tiny_overlap[1]["start"] == 1.0, "only a <=120 ms accidental overlap should be corrected"

    parse_srt = namespace["parse_srt"]
    parsed = parse_srt("""1
00:00:00,000 --> 00:00:03,000
[M] សួស្តី

2
00:00:01,300 --> 00:00:04,500
[F] ជំរាបសួរ""")
    assert [(cue["start"], cue["end"]) for cue in parsed] == [(0, 3000), (1300, 4500)]

    atempo_chain = namespace["atempo_chain"]
    assert atempo_chain(1.0) == ""
    assert atempo_chain(1.65) == "atempo=1.65000"
    assert atempo_chain(4.0) == "atempo=2.00000,atempo=2.00000"
    print("Subtitle timing and tempo regression tests passed")


if __name__ == "__main__":
    main()
