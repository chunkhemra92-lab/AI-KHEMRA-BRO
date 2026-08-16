from pathlib import Path
import subprocess
import tempfile

with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    out = root / 'four_track_test.mp3'
    command = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'sine=frequency=220:duration=2',
        '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
        '-f', 'lavfi', '-i', 'sine=frequency=660:duration=2',
        '-f', 'lavfi', '-i', 'anoisesrc=color=white:duration=2',
        '-filter_complex',
        '[0:a]highpass=f=100,equalizer=f=400:t=q:w=1:g=-5,equalizer=f=3000:t=q:w=1:g=1.5,treble=g=2:f=11000,pan=mono|c0=c0,volume=-4dB[direct];'
        '[1:a]highpass=f=180,treble=g=4:f=10000,pan=stereo|c0=c0|c1=c0,haas=left_delay=2.5:right_delay=3.5:side_gain=1.25,extrastereo=m=1.8,aecho=0.65:0.35:45|300|650|1100|1800|2600|3200:0.32|0.24|0.18|0.13|0.09|0.06|0.04,volume=-7dB[thought];'
        '[direct][thought]amix=inputs=2:duration=longest:normalize=0,asplit=2[voice_for_sc][voice_for_mix];'
        '[2:a]volume=-24dB,equalizer=f=1800:t=q:w=1:g=-4[music];'
        '[music][voice_for_sc]sidechaincompress=threshold=0.025:ratio=8:attack=12:release=300:makeup=1:link=average[music_ducked];'
        '[3:a]lowpass=f=7000,volume=-23dB[ambience];'
        '[voice_for_mix][music_ducked][ambience]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.94,aresample=48000[out]',
        '-map', '[out]', '-c:a', 'libmp3lame', '-ac', '2', '-ar', '48000', '-b:a', '128k', str(out),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(result.stderr)
    print(f'four-track FFmpeg smoke test passed: {out.stat().st_size} bytes')
