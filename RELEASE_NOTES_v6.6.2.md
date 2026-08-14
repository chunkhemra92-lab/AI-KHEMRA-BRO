# AI KHEMRA BRO v6.6.2 — Continuous Khmer Rhythm

កំណែនេះផ្តោតលើ **ចង្វាក់និយាយខ្មែរ** ដោយមិនបន្ថែម UI ឬ settings ថ្មី។

## ការកែប្រែសំខាន់

| បញ្ហា | ការកែពិតក្នុង `app.py` |
|---|---|
| សំឡេងឡើងចុះរាល់ subtitle | បន្ទាត់ SRT ដែលជាប់គ្នា មាន tag ដូចគ្នា និងគម្លាតមិនលើស 260 ms ត្រូវបានបញ្ចូលជាឃ្លាសំឡេងតែមួយ មុនផ្ញើទៅ Edge TTS។ |
| ពាក្យត្រូវបំបែកៗ | Khmer full stop នៅចុងបន្ទាត់ subtitle មុន ត្រូវដកចេញតែនៅពេលវាជាបន្ទាត់បន្តរបស់តួដដែល។ ការសួរ និងការស្រែកនៅតែរក្សាទុក។ |
| ល្បឿនធម្មតាមិនស្មើ | សំឡេង `[M]` និង `[F]` ត្រូវបានដាក់ rate `+0%` ដើម្បីឱ្យ Edge Khmer Neural ប្រើចង្វាក់ធម្មតារបស់វា។ |
| សំឡេងលោត/កន្ត្រាក់ | រក្សា no-cut rendering និងដក limiter ក្នុង cue នីមួយៗ; final mastering ស្រាលៗនៅ output នៅដដែល។ |

## អ្វីដែលមិនបានប្តូរ

UI នៅតែសាមញ្ញដូច v6.6.1។ មិនមាន music upload ឬ Audio Ducking controls បង្ហាញក្នុង workflow ទេ។ Tags `[M]`, `[F]`, `[M_THINK]` និង `[F_THINK]` នៅដដែល។ API keys និង Streamlit Secrets មិនត្រូវបានប៉ះពាល់ឡើយ។

## ការសាកល្បង

បានសាកល្បងការរួមបញ្ចូល cue Khmer តួប្រុស និងតួស្រីជាប់ៗគ្នា, no-cut MP3 ពិត, live Edge TTS, SRT workflow, video/upload tests, user isolation, Gemini hardening និង Python compile។ Regression suite ទាំងមូលបានឆ្លងកាត់។

## Deploy

ជំនួស `app.py`, `requirements.txt` និង `packages.txt` ក្នុង repository របស់អ្នក រួច reboot app នៅ Streamlit Cloud។ សូមរក្សា `COOKIE_SECRET`, `GEMINI_API_KEYS`, `LICENSE_PEPPER` និង `ADMIN_PASSWORD` ក្នុង Streamlit Secrets ដដែល។
