import asyncio
import subprocess
import tempfile
from pathlib import Path
import edge_tts

OUT = Path('voice_test_output')
OUT.mkdir(exist_ok=True)
CUES = [
    (0, 3000, 'M', 'អ្នកមកដល់ហើយ! ខ្ញុំរង់ចាំអ្នកយូរហើយណា។'),
    (3200, 6200, 'F', 'សុំទោស បង។ ផ្លូវមានបញ្ហាចរាចរណ៍ ហើយខ្ញុំមកយឺតបន្តិច។'),
    (6400, 9400, 'M_THINK', 'គាត់នៅតែយកចិត្តទុកដាក់ចំពោះខ្ញុំ... ខ្ញុំគួរតែប្រាប់ការពិតទៅគាត់។'),
    (9600, 12600, 'F_THINK', 'បើខ្ញុំប្រាប់គាត់ឥឡូវនេះ គាត់នឹងខឹងខ្ញុំទេ?'),
    (12800, 15800, 'M', 'មិនអីទេ អូន។ សំខាន់គឺអូនមកដល់ដោយសុវត្ថិភាព។'),
    (16000, 19000, 'F', 'អរគុណបង។ ពេលឮបងនិយាយបែបនេះ ខ្ញុំមានអារម្មណ៍ធូរចិត្តណាស់។'),
]
PROFILES = {
    'M': {'voice': 'km-KH-PisethNeural', 'rate': '-3%', 'pitch': '-2Hz', 'volume': '+7%'},
    'F': {'voice': 'km-KH-SreymomNeural', 'rate': '-2%', 'pitch': '-1Hz', 'volume': '+7%'},
    'M_THINK': {'voice': 'km-KH-PisethNeural', 'rate': '-7%', 'pitch': '-4Hz', 'volume': '+5%'},
    'F_THINK': {'voice': 'km-KH-SreymomNeural', 'rate': '-7%', 'pitch': '-3Hz', 'volume': '+5%'},
}
FILTERS = {
    'M': 'highpass=f=100,lowpass=f=11500,equalizer=f=400:t=q:w=1:g=-5,equalizer=f=3000:t=q:w=1:g=1.5,equalizer=f=7500:t=q:w=1:g=-1.5,pan=mono|c0=c0,volume=-4dB',
    'F': 'highpass=f=100,lowpass=f=11500,equalizer=f=400:t=q:w=1:g=-5,equalizer=f=3000:t=q:w=1:g=1.5,equalizer=f=7500:t=q:w=1:g=-1.5,pan=mono|c0=c0,volume=-4dB',
    'M_THINK': 'highpass=f=180,lowpass=f=11500,equalizer=f=7000:t=q:w=1:g=-1,pan=stereo|c0=c0|c1=c0,haas=left_delay=0.8:right_delay=1.2:side_gain=0.18,volume=-8dB',
    'F_THINK': 'highpass=f=180,lowpass=f=11500,equalizer=f=7000:t=q:w=1:g=-1,pan=stereo|c0=c0|c1=c0,haas=left_delay=0.8:right_delay=1.2:side_gain=0.18,volume=-8dB',
}

async def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        processed = []
        for idx, (start, end, tag, text) in enumerate(CUES):
            raw = root / f'raw_{idx}.mp3'
            clean = OUT / f'cue_{idx+1}_{tag}.mp3'
            profile = PROFILES[tag]
            await edge_tts.Communicate(text=text, **profile).save(str(raw))
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(raw), '-af', FILTERS[tag], '-ac', '2', '-ar', '48000', '-c:a', 'libmp3lame', '-b:a', '192k', str(clean)], check=True)
            processed.append((start, end, tag, clean))
        inputs = []
        graph = []
        labels = []
        for idx, (start, end, tag, path) in enumerate(processed):
            inputs += ['-i', str(path)]
            label = f'c{idx}'
            graph.append(f'[{idx}:a]atrim=0:{(end-start)/1000:.3f},adelay={start}|{start}[{label}]')
            labels.append(f'[{label}]')
        total = (CUES[-1][1] + 400) / 1000
        graph.append(''.join(labels) + f'amix=inputs={len(labels)}:duration=longest:normalize=0,acompressor=threshold=-18dB:ratio=1.35:attack=18:release=240,alimiter=limit=0.94,loudnorm=I=-23:TP=-4.0:LRA=9,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[out]')
        combined = OUT / 'four_tag_srt_test_combined.mp3'
        command = ['ffmpeg', '-y', *inputs, '-filter_complex', ';'.join(graph), '-map', '[out]', '-c:a', 'libmp3lame', '-ac', '2', '-ar', '48000', '-b:a', '192k', str(combined)]
        subprocess.run(command, check=True)
        print(f'combined: {combined} ({combined.stat().st_size} bytes)')
        for _, _, tag, path in processed:
            print(f'{tag}: {path}')

asyncio.run(main())
