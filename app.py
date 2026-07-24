import asyncio
import re
import subprocess
import tempfile
import os
import time
from pathlib import Path

import edge_tts
import streamlit as st

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    from google import genai
except ImportError:
    genai = None

st.set_page_config(page_title='AI KHEMRA BRO', page_icon='🎬', layout='wide', initial_sidebar_state='collapsed')


MALE_VOICE = "km-KH-PisethNeural"
FEMALE_VOICE = "km-KH-SreymomNeural"


def ms_to_srt(ms: int) -> str:
    ms = max(0, int(ms))
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def segments_to_srt(segments) -> str:
    blocks = []
    for index, segment in enumerate(segments, start=1):
        text = re.sub(r"\s+", " ", segment.text).strip()
        if not text:
            continue
        start_ms = int(float(segment.start) * 1000)
        end_ms = max(start_ms + 100, int(float(segment.end) * 1000))
        blocks.append(
            f"{index}\n{ms_to_srt(start_ms)} --> {ms_to_srt(end_ms)}\n[M] {text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


@st.cache_resource(show_spinner=False)
def load_whisper_model(model_name: str):
    if WhisperModel is None:
        raise RuntimeError("Missing faster-whisper. Add faster-whisper to requirements.txt.")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    return WhisperModel(model_name, device="cpu", compute_type=compute_type)


def transcribe_video_to_srt(video_bytes: bytes, filename: str, model_name: str) -> str:
    suffix = Path(filename).suffix or ".mp4"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        video_path = temp_path / f"input{suffix}"
        audio_path = temp_path / "audio.wav"
        video_path.write_bytes(video_bytes)

        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vn", "-ac", "1", "-ar", "16000",
                "-c:a", "pcm_s16le", str(audio_path),
            ],
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or "FFmpeg audio extraction failed")[-1800:])

        model = load_whisper_model(model_name)
        segments, _info = model.transcribe(
            str(audio_path),
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=True,
        )
        srt = segments_to_srt(list(segments))
        if not srt.strip():
            raise RuntimeError("No speech was detected in this video.")
        return srt


def split_srt_for_translation(srt_text: str, max_chars: int = 9000) -> list[str]:
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    chunks, current, size = [], [], 0
    for block in blocks:
        extra = len(block) + 2
        if current and size + extra > max_chars:
            chunks.append("\n\n".join(current))
            current, size = [], 0
        current.append(block)
        size += extra
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def translate_srt_with_gemini(srt_text: str, api_keys: list[str], model_name: str, target_language: str) -> str:
    if genai is None:
        raise RuntimeError("Missing google-genai. Add google-genai to requirements.txt.")
    if not api_keys:
        env_key = os.getenv("GEMINI_API_KEY", "").strip()
        api_keys = [env_key] if env_key else []
    if not api_keys:
        raise ValueError("GEMINI_API_KEY is missing in Railway Variables.")

    prompt = f"""You are a professional subtitle translator.
Translate the following SRT into {target_language}.
Rules:
1. Keep every subtitle number and timestamp exactly unchanged.
2. Return valid SRT only, without markdown fences or explanation.
3. Use natural spoken language suitable for movie dubbing.
4. Preserve existing speaker tags such as [M], [F], [BOY], [GIRL], [OLD_M], [OLD_F], [M_THINK], [F_THINK].
5. Do not omit dialogue.

SRT:
"""

    translated_parts = []
    chunks = split_srt_for_translation(srt_text)
    last_error = None
    for chunk_index, chunk in enumerate(chunks):
        success = False
        for key in api_keys:
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt + chunk,
                )
                text = (response.text or "").strip()
                text = re.sub(r"^```(?:srt)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
                if "-->" not in text:
                    raise RuntimeError("Gemini did not return valid SRT.")
                translated_parts.append(text)
                success = True
                break
            except Exception as exc:
                last_error = exc
        if not success:
            raise RuntimeError(f"Translation failed on part {chunk_index + 1}: {last_error}")
    return "\n\n".join(translated_parts).strip() + "\n"


def parse_srt_blocks(srt_text: str) -> list[dict]:
    """Parse SRT and return start/end milliseconds, speaker tag and clean text."""
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    items = []

    time_pattern = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
        r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
    )

    def to_ms(h: str, m: str, s: str, ms: str) -> int:
        return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue

        time_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time_index is None:
            continue

        match = time_pattern.search(lines[time_index])
        if not match:
            continue

        start_ms = to_ms(*match.groups()[:4])
        end_ms = to_ms(*match.groups()[4:])
        dialogue = " ".join(lines[time_index + 1:]).strip()

        speaker = "M"
        tag_match = re.match(
            r"^\s*\[(M|F|BOY|GIRL|OLD_M|OLD_F|M_THINK|F_THINK)\]\s*",
            dialogue,
            flags=re.I,
        )
        if tag_match:
            speaker = tag_match.group(1).upper()
            dialogue = dialogue[tag_match.end():].strip()

        # Also support dubbing XML tags.
        voice_match = re.search(r'<dubbing\s+voice="([^"]+)">', dialogue, flags=re.I)
        if voice_match:
            voice_name = voice_match.group(1)
            speaker = "F" if "Sreymom" in voice_name else "M"
            dialogue = re.sub(r"</?dubbing[^>]*>", "", dialogue, flags=re.I).strip()

        if dialogue:
            items.append(
                {
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "speaker": speaker,
                    "text": dialogue,
                }
            )

    return items


def run_async(coro):
    """Run an async coroutine safely inside Streamlit."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


VOICE_PROFILES = {
    # Normal dialogue
    "M":       {"voice": MALE_VOICE,   "rate": "+0%",  "pitch": "+0Hz",  "volume": "+0%"},
    "F":       {"voice": FEMALE_VOICE, "rate": "+0%",  "pitch": "+0Hz",  "volume": "+0%"},

    # Children: simulated using faster rate and higher pitch
    "BOY":     {"voice": MALE_VOICE,   "rate": "+8%",  "pitch": "+25Hz", "volume": "+0%"},
    "GIRL":    {"voice": FEMALE_VOICE, "rate": "+8%",  "pitch": "+28Hz", "volume": "+0%"},

    # Elderly: simulated using slower rate and lower pitch
    "OLD_M":   {"voice": MALE_VOICE,   "rate": "-12%", "pitch": "-18Hz", "volume": "-2%"},
    "OLD_F":   {"voice": FEMALE_VOICE, "rate": "-12%", "pitch": "-15Hz", "volume": "-2%"},

    # Inner thoughts: softer, slower and slightly lower
    "M_THINK": {"voice": MALE_VOICE,   "rate": "-8%",  "pitch": "-8Hz",  "volume": "-12%"},
    "F_THINK": {"voice": FEMALE_VOICE, "rate": "-8%",  "pitch": "-6Hz",  "volume": "-12%"},
}


async def synthesize_one(
    text: str,
    profile: dict,
    output_path: str,
) -> None:
    communicate = edge_tts.Communicate(
        text=text,
        voice=profile["voice"],
        rate=profile["rate"],
        volume=profile["volume"],
        pitch=profile["pitch"],
    )
    await communicate.save(output_path)


def generate_dubbed_mp3(srt_text: str, voice_mode: str) -> bytes:
    """
    Generate one synchronized MP3 with FFmpeg.

    This version does not use pydub/audioop, so it works with the newer
    Python runtime used by Streamlit Community Cloud.
    """
    segments = parse_srt_blocks(srt_text)
    if not segments:
        raise ValueError("រកមិនឃើញ SRT ដែលមាន timestamp ត្រឹមត្រូវទេ។")

    total_ms = max(item["end_ms"] for item in segments) + 500

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        clip_paths = []

        for index, item in enumerate(segments, start=1):
            if voice_mode.startswith("All Male"):
                profile = VOICE_PROFILES["M"]
            elif voice_mode.startswith("All Female"):
                profile = VOICE_PROFILES["F"]
            else:
                profile = VOICE_PROFILES.get(item["speaker"], VOICE_PROFILES["M"])

            clip_path = temp_path / f"segment_{index:04d}.mp3"
            run_async(synthesize_one(item["text"], profile, str(clip_path)))
            clip_paths.append(clip_path)

        output_path = temp_path / "khmer_dubbed_audio.mp3"

        command = ["ffmpeg", "-y"]
        for clip_path in clip_paths:
            command.extend(["-i", str(clip_path)])

        filters = []
        labels = []

        for index, item in enumerate(segments):
            slot_seconds = max(0.10, (item["end_ms"] - item["start_ms"]) / 1000)
            delay_ms = max(0, item["start_ms"])
            label = f"a{index}"
            filters.append(
                f"[{index}:a]"
                f"atrim=0:{slot_seconds:.3f},"
                f"asetpts=PTS-STARTPTS,"
                f"adelay={delay_ms}|{delay_ms}"
                f"[{label}]"
            )
            labels.append(f"[{label}]")

        total_seconds = total_ms / 1000
        filters.append(
            "".join(labels)
            + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0,"
              f"apad=whole_dur={total_seconds:.3f},"
              f"atrim=0:{total_seconds:.3f}"
              "[mixed]"
        )

        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[mixed]",
                "-ac",
                "2",
                "-ar",
                "44100",
                "-b:a",
                "128k",
                str(output_path),
            ]
        )

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            error_text = result.stderr[-1500:] if result.stderr else "FFmpeg failed."
            raise RuntimeError(error_text)

        return output_path.read_bytes()

st.markdown('''
<style>
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebarCollapsedControl"], #MainMenu, footer{display:none!important}
.stApp{background:#0b0f17;color:#fff}.hero{background:linear-gradient(145deg,#15151f,#0f1118);border:2px solid #d100ff;border-radius:26px;padding:34px 24px;text-align:center;box-shadow:0 0 30px rgba(209,0,255,.18);margin-bottom:22px}.hero h1{font-size:clamp(32px,6vw,58px);margin:0 0 10px;font-weight:800}.hero p{color:#59d9ff;font-weight:800;letter-spacing:3px;font-size:clamp(13px,2.5vw,20px);margin:0}[data-testid="stSidebar"]{background:#111827;border-right:1px solid #253044}.profile-card{border:2px solid #57d8f5;border-radius:24px;padding:22px;text-align:center;background:#1d2533;margin-bottom:18px}.status-box{border-radius:16px;padding:18px;margin:12px 0 18px;font-size:18px;font-weight:600;background:#102239;border:1px solid #17355a}.success-box{border-radius:16px;padding:18px;margin:12px 0 18px;font-size:18px;background:#075f49;border:1px solid #15d6a1}.stButton>button{width:100%;border:0;border-radius:14px;min-height:54px;font-weight:800;font-size:17px;background:linear-gradient(90deg,#8e1bcc,#e200ff);color:white}.stDownloadButton>button{width:100%;border-radius:14px;min-height:50px;font-weight:700}div[data-testid="stFileUploader"]{background:#eff3f8;border-radius:16px;padding:10px}h1,h2,h3{color:#fff}.small-note{color:#a8b3c7;font-size:13px}
div[data-testid="stTextArea"] textarea{
    background:#111827!important;color:#fff!important;border:1px solid #475569!important;
    border-radius:14px!important;font-size:17px!important;line-height:1.65!important;
    font-family:"Noto Sans Khmer","Khmer OS System",Arial,sans-serif!important;
}
.lite-card{background:#102239;border:1px solid #24527d;border-radius:16px;padding:15px;margin:10px 0}
.file-ok{background:#064e3b;border:1px solid #10b981;border-radius:16px;padding:15px;margin:10px 0}
.file-bad{background:#57151c;border:1px solid #ef4444;border-radius:16px;padding:15px;margin:10px 0}
@media(max-width:700px){
    .hero{padding:24px 12px}.hero h1{font-size:32px}.hero p{letter-spacing:1px;font-size:12px}
    .stButton>button,.stDownloadButton>button{min-height:48px;font-size:15px}
}
</style>
''', unsafe_allow_html=True)

for k, v in {'srt_text':'', 'translated_srt':'', 'generated_audio':False, 'show_video_preview':False, 'audio_bytes':None, 'tab3_audio':None}.items():
    st.session_state.setdefault(k, v)

with st.sidebar:
    st.markdown('''<div class="profile-card"><h2>🎬 AI KHEMRA BRO</h2><div>REAL WORKFLOW MODE</div><div>Video → SRT → Khmer → MP3</div></div>''', unsafe_allow_html=True)
    st.markdown('---')
    st.subheader('📶 Mobile Internet Mode')
    lite_4g = st.toggle(
        '4G Lite Mode (ណែនាំ)',
        value=True,
        help='បិទ Video Preview ស្វ័យប្រវត្តិ និងកាត់បន្ថយការប្រើទិន្នន័យ។'
    )
    max_video_mb = 60 if lite_4g else 150
    st.caption(f'ទំហំវីដេអូណែនាំ: មិនលើស {max_video_mb} MB')
    st.markdown('---')
    st.subheader('🌍 Target Language (ភាសាបកប្រែ)')
    target_language = st.selectbox('ជ្រើសរើសភាសា (Select Language):', ['Khmer (ខ្មែរ)','English','Thai','Vietnamese'])
    st.markdown('---')
    st.subheader('⚙️ AI Settings')
    railway_api_key = os.getenv('GEMINI_API_KEY', '').strip()
    valid_keys = [railway_api_key] if railway_api_key else []
    if railway_api_key:
        st.success('✅ Gemini API Key connected from Railway')
        st.caption('API Key ត្រូវបានលាក់នៅលើ Server។ អ្នកប្រើមិនអាចមើលឃើញបានទេ។')
    else:
        st.error('❌ GEMINI_API_KEY មិនទាន់បានដាក់នៅ Railway Variables ទេ។')
    st.markdown('---')
    st.subheader('🎭 Translation Style')
    st.radio('ជ្រើសរើសទម្រង់បកប្រែ:', ['Chinese Drama Pro (សម្រាប់រឿងចិន)','100% Audio Sync (កំណត់ពេលត្រូវគ្នា)','Standard (ការបកប្រែធម្មតា)'])
    st.markdown('---')
    st.subheader('⚙️ Audio Sync Mode')
    st.radio('កែតម្រូវល្បឿន:', ['Speed Up Only (លឿន)','Speed Up & Slow Down (លឿន និង យឺត)'])
    st.markdown('---')
    st.subheader('🗣️ Voice Mode (របៀបសំឡេង)')
    voice_mode = st.radio(
        'កំណត់សម្រាប់ Tab 1 និង Tab 2:',
        ['Auto (បែងចែកតាម Tag)','All Male (ប្រុសសុទ្ធ)','All Female (ស្រីសុទ្ធ)']
    )
    st.caption(
        'Tags: [M] ប្រុស • [F] ស្រី • [BOY] ក្មេងប្រុស • [GIRL] ក្មេងស្រី • '
        '[OLD_M] បុរសចាស់ • [OLD_F] ស្ត្រីចាស់ • '
        '[M_THINK] ប្រុសគិតក្នុងចិត្ត • [F_THINK] ស្រីគិតក្នុងចិត្ត'
    )
    st.markdown('---')
    st.subheader('🧠 AI Model (ម៉ូឌែល AI)')
    gemini_model = st.selectbox('ជ្រើសរើសម៉ូឌែល (Select Model):', ['gemini-2.5-flash','gemini-2.5-pro','gemini-2.0-flash'])
    whisper_model = st.selectbox('Whisper Model:', ['tiny','base','small'], index=1, help='tiny លឿនជាង; small ត្រឹមត្រូវជាង ប៉ុន្តែយឺត។')

st.markdown('''<div class="hero"><h1>AI KHEMRA BRO</h1><p>GLOBAL AI DUBBING & SUBTITLING WORKSTATION</p></div>''', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(['🎬 AI Video Dubbing','🌐 AI SRT Translator','📜 Subtitle to Speech'])

with tab1:
    st.header('1️⃣ Generate Subtitles (Khmer ខ្មែរ)')

    if lite_4g:
        st.markdown(
            '<div class="lite-card">📶 <b>4G Lite Mode កំពុងបើក</b><br>'
            'App នឹងមិនបើក Video Preview ដោយស្វ័យប្រវត្តិទេ ដើម្បីសន្សំទិន្នន័យ និងកាត់បន្ថយការយឺត។</div>',
            unsafe_allow_html=True
        )

    uploaded_video = st.file_uploader(
        f'📤 Upload Video — ណែនាំមិនលើស {max_video_mb} MB',
        type=['mp4', 'mov', 'mkv', 'avi', 'webm'],
        accept_multiple_files=False,
        key='video_uploader',
        help='MP4 (H.264) មានភាពឆបគ្នាល្អបំផុតសម្រាប់ទូរស័ព្ទ និង 4G។'
    )

    if uploaded_video is None:
        st.info('ជ្រើសរើសវីដេអូ MP4 ខ្លី។ ប៊ូតុងដំណើរការនឹងបង្ហាញក្រោយ Upload រួច។')
    else:
        size_mb = uploaded_video.size / (1024 * 1024)
        file_ext = uploaded_video.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_video.name else ''

        if size_mb > max_video_mb:
            st.markdown(
                f'<div class="file-bad">❌ វីដេអូមានទំហំ <b>{size_mb:.1f} MB</b>។ '
                f'សម្រាប់ 4G សូមបង្រួមឱ្យតិចជាង <b>{max_video_mb} MB</b> ហើយ Upload ម្តងទៀត។</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="file-ok">✅ Upload រួចរាល់<br>'
                f'📄 {uploaded_video.name}<br>📦 {size_mb:.1f} MB</div>',
                unsafe_allow_html=True
            )

            if file_ext != 'mp4':
                st.warning('សម្រាប់ 4G និងទូរស័ព្ទ សូមប្រើ MP4 ប្រសិនបើអាច។')

            # Preview is optional because it can consume more mobile data and memory.
            preview_label = '▶️ បើក Video Preview (ប្រើទិន្នន័យបន្ថែម)'
            if st.checkbox(preview_label, value=False, key='preview_checkbox'):
                st.video(uploaded_video)

            if st.button('🚀 Generate Subtitles (Real)', key='gen'):
                try:
                    progress = st.progress(5)
                    box = st.empty()
                    box.markdown('<div class="status-box">📥 Reading uploaded video...</div>', unsafe_allow_html=True)
                    video_bytes = uploaded_video.getvalue()
                    progress.progress(20)

                    box.markdown('<div class="status-box">🎧 Extracting audio and transcribing real speech...</div>', unsafe_allow_html=True)
                    original_srt = transcribe_video_to_srt(
                        video_bytes, uploaded_video.name, whisper_model
                    )
                    progress.progress(70)

                    box.markdown(f'<div class="status-box">🌐 Translating SRT into {target_language}...</div>', unsafe_allow_html=True)
                    if target_language.startswith('Khmer'):
                        st.session_state.srt_text = translate_srt_with_gemini(
                            original_srt, valid_keys, gemini_model, 'natural spoken Khmer'
                        )
                    else:
                        st.session_state.srt_text = translate_srt_with_gemini(
                            original_srt, valid_keys, gemini_model, target_language
                        )
                    progress.progress(100)
                    box.markdown('<div class="success-box">✅ Real SRT generation complete.</div>', unsafe_allow_html=True)
                except Exception as exc:
                    st.error(f'❌ ដំណើរការមិនបាន៖ {exc}')

    if st.session_state.srt_text:
        st.subheader('Generated SRT from Video')
        st.session_state.srt_text = st.text_area(
            'កែសម្រួល SRT នៅទីនេះ:',
            value=st.session_state.srt_text,
            height=420
        )

        st.download_button(
            '⬇️ Download SRT',
            st.session_state.srt_text.encode('utf-8'),
            'generated_khmer.srt',
            'application/x-subrip'
        )

        st.markdown('---')
        st.header('2️⃣ AI Dubbing (Edge TTS Studio)')

        if st.button('🎙️ Generate Dubbed Audio (MP3)', key='audio'):
            try:
                with st.spinner('កំពុងបង្កើតសំឡេង Piseth និង Sreymom...'):
                    st.session_state.audio_bytes = generate_dubbed_mp3(
                        st.session_state.srt_text,
                        voice_mode,
                    )
                st.session_state.generated_audio = True
                st.success('✅ បង្កើតសំឡេង MP3 ពិតរួចរាល់។')
            except Exception as exc:
                st.session_state.generated_audio = False
                st.session_state.audio_bytes = None
                st.error(f'❌ មិនអាចបង្កើតសំឡេងបាន៖ {exc}')

    if st.session_state.generated_audio and st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format='audio/mp3')
        st.download_button(
            '⬇️ Download Dubbed MP3',
            data=st.session_state.audio_bytes,
            file_name='khmer_dubbed_audio.mp3',
            mime='audio/mpeg',
            key='download_dubbed_mp3',
        )

    if uploaded_video is not None or st.session_state.srt_text:
        if st.button('🗑️ សម្អាត (Clear Video Project)', key='clear'):
            st.session_state.srt_text = ''
            st.session_state.generated_audio = False
            st.session_state.audio_bytes = None
            st.session_state.show_video_preview = False
            st.rerun()

with tab2:
    st.header('🌐 AI SRT Translator')
    src = st.text_area('Paste original SRT', height=320, key='translator_source')
    if st.button('🌐 Translate SRT (Real)', key='tr'):
        if not src.strip():
            st.warning('សូមបញ្ចូល SRT ជាមុនសិន។')
        else:
            try:
                with st.spinner('Gemini កំពុងបកប្រែ SRT ពិត...'):
                    language_name = 'natural spoken Khmer' if target_language.startswith('Khmer') else target_language
                    st.session_state.translated_srt = translate_srt_with_gemini(
                        src, valid_keys, gemini_model, language_name
                    )
                st.success('✅ បកប្រែ SRT រួចរាល់។')
            except Exception as exc:
                st.error(f'❌ បកប្រែមិនបាន៖ {exc}')

    st.session_state.translated_srt = st.text_area(
        'Translated SRT',
        value=st.session_state.translated_srt,
        height=320,
        key='translator_result',
    )
    if st.session_state.translated_srt.strip():
        st.download_button(
            '⬇️ Download Translated SRT',
            st.session_state.translated_srt.encode('utf-8'),
            'translated.srt',
            'application/x-subrip',
        )

with tab3:
    st.header('📜 Subtitle to Speech')
    speech = st.text_area('Paste Khmer SRT with character tags', height=360)
    st.selectbox('Male Voice', [MALE_VOICE])
    st.selectbox('Female Voice', [FEMALE_VOICE])

    if st.button('🎧 Create Speech Audio', key='speech'):
        if not speech.strip():
            st.warning('សូមបញ្ចូល SRT ជាមុនសិន។')
        else:
            try:
                with st.spinner('កំពុងបង្កើតសំឡេង Piseth និង Sreymom...'):
                    speech_audio = generate_dubbed_mp3(speech, voice_mode)
                st.session_state.tab3_audio = speech_audio
                st.success('✅ បង្កើតសំឡេងរួចរាល់។')
            except Exception as exc:
                st.error(f'❌ មិនអាចបង្កើតសំឡេងបាន៖ {exc}')

    if st.session_state.get('tab3_audio'):
        st.audio(st.session_state.tab3_audio, format='audio/mp3')
        st.download_button(
            '⬇️ Download Speech MP3',
            data=st.session_state.tab3_audio,
            file_name='subtitle_to_speech.mp3',
            mime='audio/mpeg',
            key='download_tab3_mp3',
        )

st.markdown('<p class="small-note">AI-KHEMRA-BRO • Mobile-first Streamlit interface</p>', unsafe_allow_html=True)
