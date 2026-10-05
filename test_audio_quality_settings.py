from pathlib import Path

SOURCE = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

assert "MAX_TEMPO_SPEED = 1.35" in SOURCE
assert '"audio_sync_mode": "Speed Up & Slow Down"' in SOURCE
assert "MAX_VIDEO_DURATION_SECONDS = 15 * 60" in SOURCE
assert "5.5 វិនាទីគឺសម្រាប់បែងចែក subtitle cue មួយប៉ុណ្ណោះ" in SOURCE
assert "Speed Up & Slow Down ជាជម្រើសធម្មជាតិជាង" in SOURCE
print("Audio quality and duration settings checks passed")
