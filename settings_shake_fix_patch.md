# AI KHEMRA BRO — definitive Settings shake fix

## Root cause

The Settings container was conditionally inserted and removed from the Streamlit tree. In addition, broad ancestor selectors could match the dashboard root. That combination allowed Streamlit to recalculate the page width when Settings changed state.

## CSS

Place the following rules inside the existing global `<style>` block. The `:has()` selectors intentionally use a direct `stElementContainer` child so they cannot match the entire dashboard root.

```css
html {
  overflow-y: scroll !important;
  scrollbar-gutter: stable both-edges !important;
}

body {
  overflow-x: hidden !important;
}

[data-testid="stElementContainer"]:has(.st-key-settings_drawer_toggle),
[data-testid="stElementContainer"]:has(.st-key-settings_drawer),
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer_toggle),
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer),
[data-testid="stHorizontalBlock"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer_toggle),
[data-testid="stHorizontalBlock"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer),
[data-testid="stColumn"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer_toggle),
[data-testid="stColumn"]:has(> [data-testid="stElementContainer"] .st-key-settings_drawer) {
  position: fixed !important;
  inset: 0 auto auto 0 !important;
  width: 0 !important;
  height: 0 !important;
  min-width: 0 !important;
  min-height: 0 !important;
  max-width: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
  pointer-events: none !important;
  flex: none !important;
}

.st-key-settings_drawer_toggle {
  position: fixed !important;
  top: 12px !important;
  left: 12px !important;
  z-index: 1000001 !important;
  width: 50px !important;
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
}

.st-key-settings_drawer {
  position: fixed !important;
  top: 68px !important;
  left: 12px !important;
  z-index: 1000000 !important;
  width: min(380px, calc(100vw - 38px)) !important;
  height: calc(100dvh - 92px) !important;
  max-height: calc(100dvh - 92px) !important;
  box-sizing: border-box !important;
  margin: 0 !important;
  overflow-y: auto !important;
  background: #0c1424 !important;
  border: 1px solid #23d7f2 !important;
  border-radius: 22px !important;
  contain: layout paint style !important;
  isolation: isolate !important;
  animation: none !important;
  transition: none !important;
  transform: none !important;
  will-change: auto !important;
}

.st-key-settings_drawer_toggle:has(.settings-toggle-state-open) button {
  visibility: hidden !important;
  pointer-events: none !important;
}

.st-key-settings_drawer:has(.settings-drawer-state-closed) {
  visibility: hidden !important;
  pointer-events: none !important;
}

.st-key-settings_drawer:has(.settings-drawer-state-closed) * {
  pointer-events: none !important;
}
```

## Python

Do not conditionally create the Settings container. Mount it on every authenticated run and switch only the marker element. This keeps the DOM geometry stable.

```python
if "settings_drawer_open" not in st.session_state:
    st.session_state.settings_drawer_open = False


def _open_settings_drawer():
    st.session_state.settings_drawer_open = True


def _close_settings_drawer():
    st.session_state.settings_drawer_open = False


with st.container(key="settings_drawer_toggle"):
    marker = "open" if st.session_state.settings_drawer_open else "closed"
    st.markdown(
        f'<span class="settings-toggle-state-{marker}" aria-hidden="true"></span>',
        unsafe_allow_html=True,
    )
    st.button(
        "⚙️",
        key="open_settings_drawer",
        help="Open Settings",
        on_click=_open_settings_drawer,
    )

with st.container(key="settings_drawer"):
    marker = "open" if st.session_state.settings_drawer_open else "closed"
    st.markdown(
        f'<span class="settings-drawer-state-{marker}" aria-hidden="true"></span>',
        unsafe_allow_html=True,
    )
    st.button(
        "✕ បិទ Settings",
        key="close_settings_drawer",
        use_container_width=True,
        on_click=_close_settings_drawer,
    )

    # Keep the existing Settings widgets below this point at the same indentation.
```

The open and close callbacks deliberately do not call `st.rerun()`. Streamlit reruns automatically after the callback, and the permanently mounted containers ensure that rerun does not change the workspace geometry.

## Validation

The patch should be checked with `python3 -m py_compile app.py`, the Settings regression test, and the existing translation, four-voice, subtitle timing, and voice-polish tests.
