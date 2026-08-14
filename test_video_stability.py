import ast
import io
import json
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

source_path = Path(__file__).with_name("app.py")
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
needed_functions = {"save_upload", "save_background_music_upload", "extract_audio", "parse_json_array"}
nodes = [
    node for node in tree.body
    if (isinstance(node, ast.FunctionDef) and node.name in needed_functions)
    or (
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "BACKGROUND_MUSIC_MAX_MB" for target in node.targets)
    )
]

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    namespace = {
        "Path": Path,
        "uuid": uuid,
        "shutil": shutil,
        "subprocess": subprocess,
        "re": re,
        "_ensure_project_workspace": lambda: root / "workspace",
    }
    (root / "workspace").mkdir()
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

    class Upload(io.BytesIO):
        def __init__(self, content, name):
            super().__init__(content)
            self.name = name
            self.size = len(content)

    save_upload = namespace["save_upload"]
    save_background_music_upload = namespace["save_background_music_upload"]
    extract_audio = namespace["extract_audio"]
    parse_json_array = namespace["parse_json_array"]

    saved = save_upload(Upload(b"sample-video-content", "short-test.mp4"))
    assert saved.exists() and saved.read_bytes() == b"sample-video-content"
    try:
        save_upload(Upload(b"bad", "not-video.exe"))
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported video suffix was accepted")

    music = save_background_music_upload(Upload(b"m" * 1024, "bed.mp3"))
    assert music.exists() and music.parent == root / "workspace"
    try:
        save_background_music_upload(Upload(b"bad", "not-music.exe"))
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported music suffix was accepted")

    video = root / "input.mp4"
    media_command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-f", "lavfi", "-i", "testsrc=size=160x90:rate=12",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
        "-t", "1.2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(video),
    ]
    subprocess.run(media_command, check=True, capture_output=True, text=True, timeout=30)
    wav = root / "audio.wav"
    extract_audio(video, wav, fast_mode=True)
    assert wav.exists() and wav.stat().st_size >= 1024

    payload = parse_json_array("```json\n[{\"id\": 1, \"text\": \"សួស្តី\"}]\n```")
    assert payload == [{"id": 1, "text": "សួស្តី"}]

print("Video/music upload, FFmpeg audio extraction, and JSON parsing tests: OK")
