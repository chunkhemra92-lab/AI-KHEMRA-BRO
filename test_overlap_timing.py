from pathlib import Path

source = Path("app.py").read_text(encoding="utf-8")
assert "Cues may overlap when their original SRT timestamps overlap." in source
assert "protected_end_ms = cue_end_ms" in source
assert "next_start_ms" not in source
assert "min(cue_end_ms, next_start_ms" not in source
print("overlap timing regression test passed")
