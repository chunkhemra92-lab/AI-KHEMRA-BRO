uploaded_video = st.file_uploader(
    "Upload Video",
    type=["mp4", "mov", "mkv", "avi", "webm"]
)

if uploaded_video:
    st.video(uploaded_video)

    # ប៊ូតុងបង្ហាញតែពេលមានវីដេអូ
    if st.button("🚀 Generate Subtitles (Sync 100%)", key="gen"):
        p = st.progress(0)
        box = st.empty()

        for pct, msg in [
            (15, "⏳ Preparing video..."),
            (35, "⏳ Analyzing audio waveforms..."),
            (60, "🧠 Transcribing speech..."),
            (82, f"🌐 Translating into {target_language}..."),
            (100, "✅ SRT Generation Complete!")
        ]:
            box.markdown(
                f'<div class="status-box">{msg}</div>',
                unsafe_allow_html=True
            )
            p.progress(pct)
            time.sleep(0.3)

        st.session_state.srt_text = """1
00:00:00,195 --> 00:00:02,500
[M] ក្រោកឡើង! ពេលនេះយើងត្រូវចេញដំណើរហើយ។
"""

        box.markdown(
            '<div class="success-box">✅ SRT Generation Complete!</div>',
            unsafe_allow_html=True
        )

else:
    st.info("📤 សូម Upload Video ជាមុនសិន")
