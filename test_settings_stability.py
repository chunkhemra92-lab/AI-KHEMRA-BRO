from pathlib import Path
import re

SOURCE = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

assert "def _toggle_settings_drawer():" in SOURCE
assert "def _open_settings_drawer():" in SOURCE
assert "def _close_settings_drawer():" in SOURCE
assert 'on_click=_toggle_settings_drawer' in SOURCE
assert 'on_click=_close_settings_drawer' in SOURCE
assert '.st-key-settings_drawer_toggle{position:fixed!important' in SOURCE
assert '[data-testid="stElementContainer"]:has(.st-key-settings_drawer)' in SOURCE
assert 'pointer-events:auto!important;position:fixed!important' in SOURCE
assert 'html{overflow-y:scroll!important;scrollbar-gutter:stable both-edges!important}' in SOURCE
assert 'body{overflow-x:hidden!important}' in SOURCE
assert '[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer)' in SOURCE
assert '[data-testid="stHorizontalBlock"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer)' in SOURCE
assert '[data-testid="stColumn"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer)' in SOURCE
assert '[data-testid="stVerticalBlock"]:has(.st-key-settings_drawer),' not in SOURCE
assert '[data-testid="stHorizontalBlock"]:has(.st-key-settings_drawer),' not in SOURCE
assert '[data-testid="stColumn"]:has(.st-key-settings_drawer){' not in SOURCE
assert 'animation:none!important;transition:none!important;transform:none!important;will-change:auto!important' in SOURCE
assert '.st-key-settings_drawer_toggle:has(.settings-toggle-state-open) button' not in SOURCE
assert 'animation:settings-drawer-door' not in SOURCE
assert '@keyframes settings-drawer-door' not in SOURCE

block_start = SOURCE.index('with st.container(key="settings_drawer_toggle")')
block_end = SOURCE.index('\napi_keys_text = st.session_state.get(', block_start)
block = SOURCE[block_start:block_end]
callback_block = SOURCE[SOURCE.index('def _open_settings_drawer():'):SOURCE.index('with st.container(key="settings_drawer_toggle")')]
assert 'st.rerun()' not in callback_block, "Settings callbacks must not trigger explicit reruns"
assert re.search(r'with st\.container\(key="settings_drawer"\):', block)
assert 'settings-drawer-state-open' in block
assert 'settings-drawer-state-closed' in block
assert 'if st.session_state.settings_drawer_open:' in block
print("Settings single-update stability assertions passed")
