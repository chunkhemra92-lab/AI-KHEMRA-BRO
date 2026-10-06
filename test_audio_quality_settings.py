from pathlib import Path

SOURCE = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

assert "MAX_TEMPO_SPEED = 1.18" in SOURCE
assert "MIN_TEMPO_SPEED = 0.86" in SOURCE
assert "'M_ADULT':{'voice':PISITH,'rate':'+0%','pitch':'+0Hz','volume':'+0%'}" in SOURCE
assert "'F_ADULT':{'voice':SREYMOM,'rate':'+0%','pitch':'+0Hz','volume':'+0%'}" in SOURCE
assert "'M_THINK':{'voice':PISITH,'rate':'-2%','pitch':'-1Hz','volume':'-1%'}" in SOURCE
assert "'F_THINK':{'voice':SREYMOM,'rate':'-2%','pitch':'-1Hz','volume':'-1%'}" in SOURCE
assert "aecho=0.8:0.78:110:0.18" not in SOURCE
assert "haas=left_delay=1.2:right_delay=1.8:side_gain=0.06" not in SOURCE
assert '"audio_sync_mode": "Speed Up & Slow Down"' in SOURCE
assert "MAX_VIDEO_DURATION_SECONDS = 15 * 60" in SOURCE
assert "5.5 វិនាទីគឺសម្រាប់បែងចែក subtitle cue មួយប៉ុណ្ណោះ" in SOURCE
assert "Speed Up & Slow Down ជាជម្រើសធម្មជាតិជាង" in SOURCE
print("Audio quality and duration settings checks passed")
