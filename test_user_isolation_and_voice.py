import ast
import re
import shutil
import tempfile
import uuid
from pathlib import Path

source_path = Path(__file__).with_name("app.py")
source_text = source_path.read_text(encoding="utf-8")
tree = ast.parse(source_text, filename=str(source_path))
assignments = {"PISITH", "SREYMOM", "VOICE_PROFILES", "TAG_ALIASES"}
functions = {
    "normalize_access_code", "normalize_voice_tag", "character_voice_filters",
    "clear_private_user_session", "_new_project_workspace", "_ensure_project_workspace",
    "_reset_project_workspace", "bind_workspace_to_customer", "load_private_api_keys",
}
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in assignments for name in names):
            nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in functions:
        nodes.append(node)

class FakeSessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value

class FakeStreamlit:
    def __init__(self):
        self.session_state = FakeSessionState()

fake_st = FakeStreamlit()
namespace = {
    "re": re, "st": fake_st, "Path": Path, "tempfile": tempfile,
    "uuid": uuid, "shutil": shutil,
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

# THOUGHT remains softer but no longer uses a hollow echo effect.
profiles = namespace["VOICE_PROFILES"]
assert profiles["M_THINK"] == {"voice": profiles["M_THINK"]["voice"], "rate": "-5%", "pitch": "-2Hz", "volume": "-4%"}
assert profiles["F_THINK"]["rate"] == "-5%"
assert not any(item.startswith("aecho=") for item in namespace["character_voice_filters"]("M_THINK"))
assert "hollow, reverberant, or echoing" in source_text
assert "LRA=7" in source_text

# One browser switches from ALPHA to BETA: all temporary results and the prior
# workspace are cleared, while BETA receives a fresh random workspace.
with tempfile.TemporaryDirectory() as temp_dir:
    first_workspace = Path(temp_dir) / "alpha"
    first_workspace.mkdir()
    (first_workspace / "alpha-private.mp4").write_text("private", encoding="utf-8")
    fake_st.session_state.update({
        "private_workspace_owner": "ALPHA",
        "project_workspace": str(first_workspace),
        "project_session_id": "alpha-session",
        "video_uploader_version": 4,
        "api_keys_manager": "alpha-private-key",
        "srt_text": "alpha subtitles",
        "audio_bytes": b"alpha audio",
        "translated_srt_preview": "alpha preview",
        "source_srt_text": "alpha source",
    })
    second_workspace = namespace["bind_workspace_to_customer"]("beta")
    assert fake_st.session_state["private_workspace_owner"] == "BETA"
    assert fake_st.session_state["project_workspace"] != str(first_workspace)
    assert not first_workspace.exists()
    assert second_workspace.exists()
    assert fake_st.session_state["srt_text"] == ""
    assert fake_st.session_state["audio_bytes"] is None
    assert fake_st.session_state["translated_srt_preview"] == ""
    assert "api_keys_manager" not in fake_st.session_state
    assert fake_st.session_state["video_uploader_version"] == 5

# Personal key loading no longer reads the shared license-record API-key field.
load_fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "load_private_api_keys")
load_source = ast.get_source_segment(source_text, load_fn)
assert "_load_api_keys_from_account" not in load_source
assert "cookie_manager.get(API_COOKIE_NAME)" in load_source

print("Natural thought voice and per-browser user-isolation tests: OK")
