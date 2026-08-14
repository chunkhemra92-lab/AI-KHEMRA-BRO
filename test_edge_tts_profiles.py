import ast
import asyncio
import tempfile
from pathlib import Path

import edge_tts

source_path = Path(__file__).with_name("app.py")
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
needed_assignments = {
    "PISITH", "SREYMOM", "VOICE_PROFILES", "FINAL_LEVELER_FILTER", "TAG_ALIASES",
    "DUCKING_DEFAULTS",
}
needed_functions = {
    "normalize_voice_tag", "normalize_dialogue", "prepare_tts_text", "synthesize",
    "run_async", "character_voice_filters", "voice_tone_filters", "probe_audio_duration",
    "normalized_ducking_config", "append_audio_master_filters", "create_single_voice_mp3",
}
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in needed_assignments for name in names):
            nodes.append(node)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in needed_functions:
        nodes.append(node)

namespace = {
    "re": __import__("re"), "asyncio": asyncio, "edge_tts": edge_tts,
    "tempfile": tempfile, "Path": Path, "subprocess": __import__("subprocess"),
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

text = "កុំបារម្ភអីណា ខ្ញុំនឹងដោះស្រាយវា។"

async def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        folder = Path(temp_dir)
        normal = folder / "normal.mp3"
        thought = folder / "thought.mp3"
        await namespace["synthesize"](text, namespace["VOICE_PROFILES"]["M"], normal)
        await namespace["synthesize"](text, namespace["VOICE_PROFILES"]["M_THINK"], thought)
        assert normal.exists() and normal.stat().st_size > 500
        assert thought.exists() and thought.stat().st_size > 500


asyncio.run(main())

# Text → Speech must use the same production cleanup, leveler and master chain.
polished = namespace["create_single_voice_mp3"](text, "F_THINK")
assert len(polished) > 1000

# Audio Ducking uses a real music input, FFmpeg sidechaincompress and a polished MP3 output.
with tempfile.TemporaryDirectory() as temp_dir:
    music = Path(temp_dir) / "music.mp3"
    made_music = namespace["subprocess"].run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
            "-i", "sine=frequency=160:sample_rate=48000:duration=1.5",
            "-c:a", "libmp3lame", "-b:a", "128k", str(music),
        ],
        capture_output=True, text=True, timeout=30,
    )
    assert made_music.returncode == 0, made_music.stderr
    ducked = namespace["create_single_voice_mp3"](
        text, "M", background_music_path=music,
        ducking_config={"enabled": True, "music_gain": 0.42, "ratio": 8, "release_ms": 700},
    )
    assert len(ducked) > 1000

print("Live Edge-TTS Khmer profiles, polished speech, and Audio Ducking: OK")
