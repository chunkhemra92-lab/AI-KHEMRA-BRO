"""Regression tests for bounded Edge TTS retries and partial-output cleanup."""

import ast
import asyncio
import re
import tempfile
from pathlib import Path

SOURCE = Path("app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
REQUIRED = {"normalize_dialogue", "prepare_tts_text", "synthesize"}
NODES = [
    node for node in TREE.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in REQUIRED
]


class FlakyCommunicate:
    calls = 0

    def __init__(self, **_kwargs):
        pass

    async def save(self, destination):
        type(self).calls += 1
        output = Path(destination)
        output.write_bytes(b"partial")
        if type(self).calls == 1:
            raise RuntimeError("temporary provider failure")
        output.write_bytes(b"a" * 700)


class EmptyCommunicate:
    calls = 0

    def __init__(self, **_kwargs):
        pass

    async def save(self, destination):
        type(self).calls += 1
        Path(destination).write_bytes(b"too-small")


def build_namespace(communicate_cls):
    edge_tts = type("EdgeTts", (), {"Communicate": communicate_cls})
    namespace = {
        "asyncio": asyncio,
        "edge_tts": edge_tts,
        "EDGE_TTS_REQUEST_TIMEOUT_SECONDS": 2,
        "PISITH": "km-KH-PisethNeural",
        "Path": Path,
        "re": re,
    }
    exec(compile(ast.Module(body=NODES, type_ignores=[]), "app.py", "exec"), namespace)
    return namespace


def main():
    profile = {"voice": "km-KH-PisethNeural", "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "voice.mp3"
        FlakyCommunicate.calls = 0
        synthesize = build_namespace(FlakyCommunicate)["synthesize"]
        asyncio.run(synthesize("សួស្តី", profile, target))
        assert FlakyCommunicate.calls == 2, "temporary provider failure should retry once"
        assert target.exists() and target.stat().st_size == 700, "retry must replace the partial file"

        target.unlink()
        EmptyCommunicate.calls = 0
        synthesize = build_namespace(EmptyCommunicate)["synthesize"]
        try:
            asyncio.run(synthesize("សួស្តី", profile, target))
        except RuntimeError as exc:
            assert "Edge TTS" in str(exc)
        else:
            raise AssertionError("undersized provider files must fail after bounded retries")
        assert EmptyCommunicate.calls == 3, "invalid output should use all three bounded attempts"
        assert not target.exists(), "invalid partial output must be removed"

    print("Edge TTS resilience regression tests passed")


if __name__ == "__main__":
    main()
