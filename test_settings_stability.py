from pathlib import Path
import re

SOURCE = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

assert "def _open_settings_drawer():" in SOURCE
assert "def _close_settings_drawer():" in SOURCE
assert 'on_click=_open_settings_drawer' in SOURCE
assert 'on_click=_close_settings_drawer' in SOURCE
assert '.st-key-settings_drawer_toggle{position:fixed!important' in SOURCE
assert '[data-testid="stElementContainer"]:has(.st-key-settings_drawer)' in SOURCE
assert 'pointer-events:auto!important;position:fixed!important' in SOURCE
assert '@keyframes settings-drawer-door' in SOURCE

block = SOURCE[SOURCE.index('with st.container(key="settings_drawer_toggle")'):SOURCE.index('        # Reference-style account card', SOURCE.index('with st.container(key="settings_drawer_toggle")'))]
assert 'st.rerun()' not in block, "Settings controls must not trigger duplicate explicit reruns"
assert re.search(r'with st\.container\(key="settings_drawer"\):', block)
print("Settings single-update stability assertions passed")
