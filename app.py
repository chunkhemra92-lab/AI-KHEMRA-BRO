# Replace render_sidebar() and the main UI area with this snippet.
# Drop this into app.py (overwrite the existing render_sidebar function).
import streamlit as st
from datetime import datetime, date
from pathlib import Path

def render_sidebar() -> dict:
    # Khmer UI based on your snippet — uses secrets for safe keys where possible.
    with st.sidebar:
        st.markdown("""
        <div style='background-color: #1E2130; padding: 15px; border-radius: 10px; border: 1px solid #00FFFF;'>
            <h3>👋 {username}</h3>
            <p><b>ROLE:</b> {role}<br>
            📅 <b>PLAN:</b> {expiry}<br>
            ⏳ <b>{days_left} DAYS LEFT</b></p>
        </div>
        """.format(
            username=secret_value("APP_USERNAME", "somevut036"),
            role=secret_value("APP_ROLE", "SOMEVUT036"),
            expiry=secret_value("PLAN_EXPIRY", "2027-06-30"),
            days_left=max(0, (datetime.strptime(secret_value("PLAN_EXPIRY", "2027-06-30"), "%Y-%m-%d").date() - date.today()).days)
        ), unsafe_allow_html=True)
        if st.button("🚪 ចាកចេញ (Logout)", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.session_token = ""
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎭 Translation Style")
        style = st.radio("ជ្រើសរើសទម្រង់បកប្រែ៖", ["Chinese Drama Pro", "100% Audio Sync", "Standard"], index=0)

        st.markdown("### ⚙️ Audio Sync Mode")
        sync_mode = st.radio("កម្រិតល្បឿនអាន៖", ["Speed Up Only", "Speed Up & Slow Down"], index=0)

        st.markdown("### 🗣️ Voice Mode (ជម្រើសសំឡេង)")
        voice_mode = st.radio("កំណត់សម្រាប់ Tab 1 & Tab 2:", ["Auto", "All Male", "All Female"], index=0)

        st.markdown("### 🧠 AI Model (ម៉ូដែល AI)")
        # Map friendly names to your internal model names
        ai_model_choice = st.selectbox("ជ្រើសរើសម៉ូដែល (Select Model):", ["gemini-2.5-flash", "gemini-2.5-flash-lite"])

        st.markdown("### 🌍 Target Language (ភាសាបកប្រែ)")
        target_lang = st.selectbox("ជ្រើសរើសភាសា (Select Language):", ["Khmer", "English"])

        st.markdown("### 🔑 API Keys Manager")
        st.markdown("Use Streamlit Secrets or environment variables for API keys. Do NOT paste production keys here.")
        # Show a small hint about the current key status
        has_key = bool(secret_value("GEMINI_API_KEY"))
        st.caption("Gemini API: " + ("connected" if has_key else "missing"))

    # Map ai_model_choice to the internal gemini_model
    gemini_model = ai_model_choice

    return {
        "style": style,
        "sync_mode": sync_mode,
        "voice_mode": voice_mode,
        "gemini_model": gemini_model,
        "whisper_model": DEFAULT_WHISPER_MODEL,
        "target_lang": target_lang,
    }

# Tabs UI: Replace the UI blocks in main() after settings/gemini_key detection with this tabs layout.
# The following assumes variables: settings (from render_sidebar), gemini_key (secret_value("GEMINI_API_KEY"))
tab1, tab2, tab3 = st.tabs(["🎬 AI Video Dubbing", "🌐 AI SRT Translator", "📜 Subtitle to Speech"])

with tab1:
    st.header(f"1️⃣ Generate Subtitles ({settings.get('target_lang','Khmer')})")
    st.markdown("**Upload Video**")
    uploaded_file = st.file_uploader("", type=["mp4", "mov", "mkv", "avi", "webm"])
    if uploaded_file is not None:
        size_mb = len(uploaded_file.getvalue()) / (1024*1024)
        st.markdown(f"**{uploaded_file.name}** — {size_mb:.1f} MB")
    if st.button("🚀 Generate Subtitles (Sync 100%)", use_container_width=True, disabled=(uploaded_file is None or not gemini_key)):
        # Trigger the same flow as before — call into your generate logic
        st.info("Starting transcription + translation... (this uses Whisper + Gemini)")
        # The real logic from your app should run here: create temp dir, run transcribe_video, translate_and_classify_srt, etc.

with tab2:
    st.header("SRT Editor & Translation")
    srt_text = st.text_area("Generated / Paste SRT here", value=st.session_state.get("translated_srt",""), height=300)
    if st.button("Translate SRT with Gemini", use_container_width=True, disabled=not gemini_key):
        st.info("Translating SRT via Gemini...")
        # Call translate_and_classify_srt(srt_text, gemini_key, settings['gemini_model'], settings['style'])

with tab3:
    st.header("Subtitle to Speech (TTS)")
    st.markdown("Upload or reuse the translated SRT and generate multi-voice MP3/MP4.")
    st.text_area("SRT for TTS", value=st.session_state.get("translated_srt",""), height=200)
    if st.button("🎙️ Generate Dubbed Audio (MP3)", use_container_width=True, disabled=not st.session_state.get("translated_srt")):
        st.info("Generating TTS — this can take some time.")
        # Call parse_srt + create_dubbed_audio + merge_video_audio as in the original flow
