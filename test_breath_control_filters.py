"""Guard against reintroducing harsh breathiness into the four voice paths."""

from pathlib import Path

SOURCE = Path("app.py").read_text(encoding="utf-8")

NORMAL_DEESSER = "deesser=i=0.22:m=0.38:f=0.54:s=o"
THOUGHT_DEESSER = "deesser=i=0.18:m=0.32:f=0.54:s=o"

assert SOURCE.count(NORMAL_DEESSER) >= 2, "Normal voice paths must de-ess breath and sibilance"
assert SOURCE.count(THOUGHT_DEESSER) >= 2, "Thought voice paths must de-ess breath and sibilance"
assert "'lowpass=f=6500:p=2'" in SOURCE, "Normal SRT dialogue must have a breath-control ceiling"
assert "'lowpass=f=7200:p=2'" in SOURCE, "Thought SRT dialogue must have a breath-control ceiling"
assert "'lowpass=f=6000:p=2'" in SOURCE, "Standalone normal TTS must have a breath-control ceiling"
assert "'lowpass=f=6400:p=2'" in SOURCE, "Standalone thought TTS must have a breath-control ceiling"
assert "'aecho=0.8:0.78:110:0.18'" in SOURCE, "Thought reflection must remain restrained"
print("four-role breath-control regression assertions passed")
