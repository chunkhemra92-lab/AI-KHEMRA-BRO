"""Validate FFmpeg polish filters for all four locked voice roles."""

import ast
import re
import subprocess
import tempfile
from pathlib import Path

SOURCE = Path("app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
REQUIRED = {"_voice_tag_key", "compact_voice_tag", "lock_voice_tag", "character_voice_filters", "polish_tts_output"}
NODES = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in REQUIRED]
namespace = {
    "FFMPEG_CLIP_CONVERSION_TIMEOUT_SECONDS": 180,
    "LOCKED_VOICE_TAGS": frozenset({"M", "F", "M_THINK", "F_THINK"}),
    "Path": Path,
    "re": re,
    "subprocess": subprocess,
}
exec(compile(ast.Module(body=NODES, type_ignores=[]), "app.py", "exec"), namespace)


def channels(path: Path) -> int:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return int(result.stdout.strip())


def main():
    polish = namespace["polish_tts_output"]
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source.mp3"
        subprocess.run(
            [
                "ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i",
                "sine=frequency=440:sample_rate=24000:duration=1.2", "-c:a", "libmp3lame", str(source),
            ],
            check=True,
            timeout=30,
        )
        for tag in ("M", "F", "M_THINK", "F_THINK"):
            output = root / f"{tag}.mp3"
            polish(source, output, tag)
            assert output.exists() and output.stat().st_size > 1000, f"{tag} polish output is invalid"
            assert channels(output) == 2, f"{tag} polished output must be stereo"
    print("four-role voice polish filter regression tests passed")


if __name__ == "__main__":
    main()
