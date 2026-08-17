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
    "VOICE_THOUGHT_RELATIVE_GAIN_DB": -1.5,
    "FINAL_MASTER_TARGET_LUFS": -16,
    "FINAL_MASTER_TRUE_PEAK_DB": -1.5,
    "LOCKED_VOICE_TAGS": frozenset({"M", "F", "M_THINK", "F_THINK"}),
    "Path": Path,
    "re": re,
    "subprocess": subprocess,
}
exec(compile(ast.Module(body=NODES, type_ignores=[]), "app.py", "exec"), namespace)


def integrated_lufs(path: Path) -> float:
    result = subprocess.run(
        [
            "ffmpeg", "-nostdin", "-i", str(path), "-filter_complex", "ebur128=peak=true",
            "-f", "null", "-",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    matches = re.findall(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", result.stderr)
    assert matches, f"Could not measure EBU R128 loudness for {path.name}"
    return float(matches[-1])


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
                "sine=frequency=440:sample_rate=48000:duration=4", "-c:a", "libmp3lame", str(source),
            ],
            check=True,
            timeout=30,
        )
        loudness = {}
        for tag in ("M", "F", "M_THINK", "F_THINK"):
            output = root / f"{tag}.mp3"
            polish(source, output, tag)
            assert output.exists() and output.stat().st_size > 1000, f"{tag} polish output is invalid"
            assert channels(output) == 2, f"{tag} polished output must be stereo"
            loudness[tag] = integrated_lufs(output)

        normal_spread = abs(loudness["M"] - loudness["F"])
        thought_spread = abs(loudness["M_THINK"] - loudness["F_THINK"])
        overall_spread = max(loudness.values()) - min(loudness.values())
        assert normal_spread <= 0.8, f"Normal voice loudness spread too high: {normal_spread:.2f} LU"
        assert thought_spread <= 0.8, f"Thought voice loudness spread too high: {thought_spread:.2f} LU"
        assert overall_spread <= 2.4, f"Four-role loudness spread too high: {overall_spread:.2f} LU"
    print("four-role voice polish and loudness-balance regression tests passed")


if __name__ == "__main__":
    main()
