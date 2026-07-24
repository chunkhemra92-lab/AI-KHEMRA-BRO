import streamlit as st

# ១. ការកំណត់ទំព័រ (Page Config)
st.set_page_config(page_title="Matly Dubber Pro", page_icon="🎬", layout="centered")

# ២. ផ្នែកចំហៀង (Sidebar - សម្រាប់ការកំណត់ផ្សេងៗ)
with st.sidebar:
    # ព័ត៌មានគណនី
    st.markdown("""
    <div style='background-color: #1E2130; padding: 15px; border-radius: 10px; border: 1px solid #00FFFF;'>
        <h3>👋 somevut036</h3>
        <p><b>ROLE:</b> SOMEVUT036<br>
        📅 <b>PLAN:</b> 2027-06-30<br>
        ⏳ <b>341 DAYS LEFT</b></p>
    </div>
    """, unsafe_allow_html=True)
    st.button("🚪 ចាកចេញ (Logout)", use_container_width=True)
    
    st.markdown("---")
    
    # ការកំណត់មុខងារ AI
    st.markdown("### 🎭 Translation Style")
    trans_style = st.radio("ជ្រើសរើសទម្រង់បកប្រែ៖", ["Chinese Drama Pro (ស្តាយ៍រឿងចិនអាជីព)", "100% Audio Sync (ភាសានិយាយទូទៅ)", "Standard (បកប្រែផ្លូវការ)"])
    
    st.markdown("### ⚙️ Audio Sync Mode")
    sync_mode = st.radio("កម្រិតល្បឿនអាន៖", ["Speed Up Only (លឿន)", "Speed Up & Slow Down (លឿន និង យឺត)"])
    
    st.markdown("### 🗣️ Voice Mode (ជម្រើសសំឡេង)")
    voice_mode = st.radio("កំណត់សម្រាប់ Tab 1 & Tab 2:", ["Auto (ប្រុស/ស្រី តាម Tag)", "All Male (ប្រុសសុទ្ធ)", "All Female (ស្រីសុទ្ធ)"])
    
    st.markdown("### 🧠 AI Model (ម៉ូដែល AI)")
    ai_model = st.selectbox("ជ្រើសរើសម៉ូដែល (Select Model):", ["gemini-3.5-flash", "gemini-pro"])
    
    st.markdown("### 🌍 Target Language (ភាសាបកប្រែ)")
    target_lang = st.selectbox("ជ្រើសរើសភាសា (Select Language):", ["Khmer (ខ្មែរ)", "English"])
    
    st.markdown("### 🔑 API Keys Manager")
    api_key = st.text_area("Paste Gemini API Keys (One per line)", "AQ.Ab8RN6JRVN2204Q-\n0HkI8kYYSm4LgX7eRLq-\nBqSGcEeugRPXUw")
    st.success("✅ កំពុងប្រើប្រាស់ 1 Keys")

# ៣. ផ្ទាំងបង្ហាញធំ (Main Content)
st.markdown("""
<div style='text-align: center; background-color: #141522; padding: 20px; border-radius: 15px; border: 2px solid #8A2BE2;'>
    <h1 style='color: white; margin-bottom: 0;'>Matly Dubber Pro</h1>
    <h5 style='color: #00FFFF; margin-top: 5px;'>GLOBAL AI DUBBING & SUBTITLING WORKSTATION</h5>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# បែងចែកជា Tabs ដូចក្នុងរូប
tab1, tab2, tab3 = st.tabs(["🎬 AI Video Dubbing", "🌐 AI SRT Translator", "📜 Subtitle to Speech"])

with tab1:
    st.header(f"1️⃣ Generate Subtitles ({target_lang})")
    
    st.markdown("**Upload Video**")
    uploaded_file = st.file_uploader("", type=["mp4", "mov", "avi"])
    
    # ប៊ូតុងបង្កើត Subtitle
    st.button("🚀 Generate Subtitles (Sync 100%)", type="primary", use_container_width=True)
    
    # ស្ថានភាពកំពុងដំណើរការ (Mockup)
    st.info("🧠 Transcribing & Translating into Khmer (ខ្មែរ)...")
    
    st.subheader("Generated SRT from Video")
    st.markdown("ពិនិត្យ និងកែសម្រួលអត្ថបទ SRT ទីនេះមុនពេលបញ្ចូលសំឡេង៖")
    
    # អត្ថបទ SRT គំរូ
    srt_mockup = """1\n00:00:00,195 --> 00:00:02,500\n[M] គ្រាន់តែត្រូវស្រលាញ់ ក៏មានអានុភាពខ្លាំងដល់ថ្នាក់នេះដែរ!\n\n2\n00:00:03,209 --> 00:00:06,500\n[M] ទោះបីជាត្រូវរងចាំនាងកំពុងយំក៏ដោយ យើងក៏មិនប្រាកដថាចាញ់ដែរ។"""
    st.text_area("", srt_mockup, height=250)
    
    st.header("2️⃣ AI Dubbing (Edge TTS Studio)")
    st.button("🎙️ Generate Dubbed Audio (MP3)", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("🗑️ ធ្វើថ្មី (Clear Video Project)", use_container_width=True)

