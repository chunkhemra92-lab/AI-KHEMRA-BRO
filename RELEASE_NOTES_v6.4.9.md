# AI KHEMRA BRO v6.4.9 — Natural Audio & Animated UI

កំណែនេះផ្តោតលើការធ្វើឱ្យសំឡេងខ្មែររលូនជាងមុន និងធ្វើឱ្យផ្នែកបកប្រែ/បង្កើតសំឡេងមានភាពច្បាស់លាស់ទំនើបសម្រាប់ទូរស័ព្ទ។ លំហូរដើមរបស់កម្មវិធី, Access Code មួយសម្រាប់ Customer ម្នាក់, ការបំបែកទិន្នន័យតាម browser និងការគាំទ្រភាសាចិន កូរ៉េ វៀតណាម និងអង់គ្លេស មិនត្រូវបានផ្លាស់ប្តូរ។

## ការកែលម្អសំឡេង

| ផ្នែក | ការកែប្រែ | ផលប៉ះពាល់រំពឹងទុក |
|---|---|---|
| Fade រវាង cue | Fade-in `0.018s`, fade-out `0.030s` | កាត់បន្ថយសំឡេងធ្លាក់ ឬដាច់ខ្លាំងនៅ cue ជាប់ៗគ្នា។ |
| ចន្លោះ cue | `MIN_VOICE_GAP_MS = 0` | រក្សា timing ដើមរបស់ SRT ដោយមិនបន្ថែមភាពស្ងាត់បង្ខំ។ |
| ល្បឿន TTS | `MAX_TEMPO_SPEED = 1.10` | មិនបង្ខំឱ្យ Edge TTS និយាយលឿនពេកពេល cue ខ្លី។ |
| Per-clip compression | Ratio `1.28`, attack `60ms`, release `400ms`, makeup `1.00` | បន្ថយការឡើងខ្លាំង/ធ្លាក់ខ្លាំងដោយទុក intonation ធម្មជាតិ។ |
| Master compression | Ratio `1.18`, attack `90ms`, release `520ms`, makeup `1.00` | រក្សាកម្រិតសំឡេងទាំង MP3 ឱ្យស្ថិរភាពជាងមុន។ |
| Master normalization | `loudnorm I=-17:TP=-2.0:LRA=7` | សំឡេងសរុបស្តាប់ទន់ និងមាន dynamic range សមរម្យ។ |
| Thought voices | គ្មាន echo | `[M_THINK]` និង `[F_THINK]` នៅស្រាលបែបគិតក្នុងចិត្ត ប៉ុន្តែមិនស្តាប់ដូចក្នុងពាង។ |

## ការកែលម្អ UI

ប៊ូតុងបកប្រែ SRT ទៅខ្មែរមានរូប **ខួរក្បាលមានចលនា** ដើម្បីបង្ហាញថាជាការងាររបស់ AI translation។ ផ្ទាំងបង្កើតសំឡេងទាំងអស់បង្ហាញកាតមីក្រូហ្វូនមានចលនា 4 ប្រភេទសម្រាប់ `[M]`, `[F]`, `[M_THINK]`, និង `[F_THINK]`។ ផ្ទាំងរង់ចាំនៅតែប្រើ waiting card ស្ងប់ស្ងាត់ដោយគ្មានភាគរយ ឬពេលវេលាលោតរញ៉េរញ៉ៃ។

## ការផ្ទៀងផ្ទាត់ដែលបានបញ្ចប់

ការសាកល្បងបានឆ្លងកាត់ទាំងអស់៖ audio/UI smoothing, Gemini API hardening, ច្បាប់បកប្រែ និង SRT tags, video upload/FFmpeg/JSON, browser-user isolation, live Edge TTS Khmer profiles, និង waiting-card/fast-ASR regression។ កម្មវិធីក៏បានចាប់ផ្តើមជោគជ័យក្នុងម៉ាស៊ីនមូលដ្ឋាន ហើយបានពិនិត្យមើល UI ក្រោយ login ដោយផ្ទាល់។

> គុណភាពធម្មជាតិចុងក្រោយនៅតែអាស្រ័យលើសំឡេងដែល Edge TTS ផ្តល់ និងអត្ថបទ SRT។ SRT ដែលសរសេរខ្លី រលូន និងមានស្លាក `[M]`, `[F]`, `[M_THINK]`, `[F_THINK]` ត្រឹមត្រូវ នឹងឱ្យលទ្ធផលល្អបំផុត។

## ដាក់ឡើង Streamlit Community Cloud

ដាក់ជំនួស `app.py`, `requirements.txt` និង `packages.txt` ក្នុង repository របស់អ្នក ហើយ reboot app។ កុំដាក់ `licenses.db` ឬ API key របស់អ្នកក្នុង Git repository។ កំណត់ secrets នៅ Streamlit Cloud ដូចកំណែចាស់៖ `COOKIE_SECRET`, `GEMINI_API_KEYS`, `LICENSE_PEPPER`, និង `ADMIN_PASSWORD`។
