"""Generate production-equivalent reference MP3s for the four public voice roles."""

import ast
import asyncio
import json
import re
import subprocess
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
OUTPUT_DIR = ROOT / "four_voice_reference_samples"

PISITH = "km-KH-PisethNeural"
SREYMOM = "km-KH-SreymomNeural"
PROFILES = {
    "M": {"voice": PISITH, "rate": "-1%", "pitch": "+0Hz", "volume": "+2%"},
    "F": {"voice": SREYMOM, "rate": "-1%", "pitch": "+0Hz", "volume": "+2%"},
    "M_THINK": {"voice": PISITH, "rate": "-4%", "pitch": "-1Hz", "volume": "+0%"},
    "F_THINK": {"voice": SREYMOM, "rate": "-4%", "pitch": "-1Hz", "volume": "+0%"},
}
SAMPLE_TEXT = "សួស្តី។ នេះជាសំឡេងខ្មែរសាកល្បងសម្រាប់វីដេអូ Facebook។"

REQUIRED = {
    "_voice_tag_key", "compact_voice_tag", "lock_voice_tag", "normalize_dialogue",
    "prepare_tts_text", "synthesize", "character_voice_filters", "polish_tts_output",
}
NODES = [
    node for node in TREE.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in REQUIRED
]
NAMESPACE = {
    "asyncio": asyncio,
    "edge_tts": edge_tts,
    "FFMPEG_CLIP_CONVERSION_TIMEOUT_SECONDS": 180,
    "FINAL_MASTER_TARGET_LUFS": -16,
    "FINAL_MASTER_TRUE_PEAK_DB": -1.5,
    "LOCKED_VOICE_TAGS": frozenset(PROFILES),
    "Path": Path,
    "PISITH": PISITH,
    "re": re,
    "SREYMOM": SREYMOM,
    "subprocess": subprocess,
    "VOICE_THOUGHT_RELATIVE_GAIN_DB": -1.5,
    "EDGE_TTS_REQUEST_TIMEOUT_SECONDS": 75,
}
exec(compile(ast.Module(body=NODES, type_ignores=[]), "app.py", "exec"), NAMESPACE)


def integrated_lufs(path: Path) -> float:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-i", str(path), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    matches = re.findall(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", result.stderr)
    if not matches:
        raise RuntimeError(f"Cannot measure loudness: {path.name}")
    return float(matches[-1])


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    synthesis = NAMESPACE["synthesize"]
    polish = NAMESPACE["polish_tts_output"]
    metrics = {}
    for tag, profile in PROFILES.items():
        raw = OUTPUT_DIR / f"{tag.lower()}_raw.mp3"
        output = OUTPUT_DIR / f"{tag.lower()}_facebook_ready.mp3"
        raw.unlink(missing_ok=True)
        output.unlink(missing_ok=True)
        await synthesis(SAMPLE_TEXT, profile, raw)
        polish(raw, output, tag)
        raw.unlink(missing_ok=True)
        metrics[tag] = {
            "file": output.name,
            "bytes": output.stat().st_size,
            "integrated_lufs": integrated_lufs(output),
        }
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
