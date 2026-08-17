from pathlib import Path

SOURCE = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

assert 'THEME_MODE_OPTIONS = ("Dark", "Light")' in SOURCE
assert '"theme_mode": "Dark"' in SOURCE
assert 'if st.session_state.get("theme_mode") not in THEME_MODE_OPTIONS:' in SOURCE
assert 'st.session_state.theme_mode = "Dark"' in SOURCE
assert 'class="theme-mode-{st.session_state.theme_mode.lower()}"' in SOURCE
assert 'key="theme_mode"' in SOURCE
assert 'on_change=account_settings_changed' in SOURCE
assert '"🌙 Dark Mode" if value == "Dark" else "☀️ Light Mode"' in SOURCE
assert '.theme-mode-dark,.theme-mode-light{display:none!important}' in SOURCE
assert 'body:has(.theme-mode-light) .st-key-settings_drawer' in SOURCE
assert 'body:has(.theme-mode-light) [data-testid="stFileUploader"] section' in SOURCE
assert 'body:has(.theme-mode-light) .stButton>button' in SOURCE
assert 'position:fixed!important' in SOURCE
print("Persistent Dark/Light theme regression assertions passed")
