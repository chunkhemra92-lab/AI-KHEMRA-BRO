from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

SOURCE_PATH = Path(__file__).with_name("app.py")
source = SOURCE_PATH.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(SOURCE_PATH))

functions = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
duplicates = sorted(name for name, count in Counter(functions).items() if count > 1)
assert not duplicates, f"Duplicate function definitions: {duplicates}"
assert source.count("def video_to_srt(") == 1, "Exactly one video_to_srt implementation must remain active"
assert "EDGE_TTS_MAX_CONCURRENT_REQUESTS = 2" in source, "Edge TTS must use the audited two-request limit"

subprocess_without_timeout: list[int] = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess" and node.func.attr in {"run", "Popen"}:
            if node.func.attr == "run" and not any(keyword.arg == "timeout" for keyword in node.keywords):
                subprocess_without_timeout.append(node.lineno)
assert not subprocess_without_timeout, f"subprocess.run calls without timeout: {subprocess_without_timeout}"

settings_start = source.index("def _toggle_settings_drawer():")
settings_end = source.index('with st.container(key="settings_drawer_toggle")', settings_start)
settings_callbacks = source[settings_start:settings_end]
assert "st.rerun()" not in settings_callbacks, "Settings callbacks must not call st.rerun()"
assert 'st.session_state.settings_drawer_open = not st.session_state.settings_drawer_open' in settings_callbacks

required_css = [
    'scrollbar-gutter:stable both-edges!important',
    'body{overflow-x:hidden!important}',
    '[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer)',
    '.st-key-settings_drawer:has(.settings-drawer-state-closed){display:none!important',
]
for marker in required_css:
    assert marker in source, f"Missing required CSS safeguard: {marker}"

unsafe_root_markers = [
    '[data-testid="stVerticalBlock"]:has(.st-key-settings_drawer),',
    '[data-testid="stHorizontalBlock"]:has(.st-key-settings_drawer),',
]
for marker in unsafe_root_markers:
    assert marker not in source, f"Unsafe broad selector is present: {marker}"

print(f"Static source audit passed: {len(functions)} functions, one subtitle pipeline, bounded subprocesses, two-request Edge TTS, and stable Settings callbacks.")
