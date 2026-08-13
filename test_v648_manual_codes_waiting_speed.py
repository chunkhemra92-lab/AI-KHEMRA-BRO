from pathlib import Path

source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

# Owner keeps the existing one-customer/one-code workflow; bulk-code UI is removed.
assert "def create_access_code_batch" not in source
assert "bulk_license_form" not in source
assert "Owner បង្កើត Access Code ម្តងមួយ" in source
assert "create_license_form" in source

# All user-facing processing flows use the same calm waiting-card style.
assert source.count('class="khemra-wait-card"') >= 5
assert "with st.spinner(" not in source
waiting_sections = source[source.index('with tab_video:'):source.index('st.caption("AI-KHEMRA-BRO')]
assert "⏱️ {int(percent)}%" not in waiting_sections
assert "{minutes:02d}:{seconds:02d}" not in waiting_sections

# Natural TTS and fast ASR tuning remain active.
assert "MAX_TEMPO_SPEED = 1.16" in source
assert "beam_size = 3 if fast_mode else 5" in source
assert "best_of = 1 if fast_mode else 3" in source
assert "aecho=" not in source
assert "Do not make the Khmer voice rush, drag, flatten its tone" in source
assert "Only [M] for male dialogue" in source
assert "[F_THINK]" in source

print("v6.4.8 manual-code, modern-waiting, voice, and fast-ASR checks: OK")
