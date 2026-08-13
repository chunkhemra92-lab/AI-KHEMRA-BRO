# AI KHEMRA BRO v6.4.3 — Video and Gemini Stability Audit

កំណែនេះបន្តពី v6.4.2 ហើយផ្តោតលើស្ថិរភាពនៃការផ្ទុកវីដេអូ, FFmpeg/Whisper, JSON response ពី Gemini និងការសម្អាតឯកសារបណ្ដោះអាសន្ន។ UI ដើម, login, menu, API-key storage និងលំហូរវីដេអូស្វ័យប្រវត្តិត្រូវបានរក្សាទុកដដែល។

## លទ្ធផលសវនកម្ម និងការកែលម្អ

| ផ្នែក | ហានិភ័យពីមុន | ការកែលម្អ v6.4.3 |
|---|---|---|
| Upload វីដេអូ | Upload ខូច ឬឯកសារទទេអាចទៅដល់ FFmpeg/Whisper | ពិនិត្យប្រភេទ `.mp4`, `.mov`, `.mkv`, `.webm`, ទំហំឯកសារបន្ទាប់ពីរក្សាទុក និងលុប partial file ពេលបរាជ័យ។ |
| ការរក្សាទុកវីដេអូ | កំហុសពេល save អាចកើតក្រៅ error handler | ការរក្សាទុកចូលក្នុង `try/finally` ហើយបង្ហាញសារ error ស្អាត និងលុប temp file ប្រសិនបើមាន។ |
| FFmpeg | Log វែង ឬ timeout អាចធ្វើឱ្យពិបាករកកំហុស | ប្រើ log level តិច, `-nostdin`, timeout handling, ពិនិត្យ audio output មិនទទេ និងសារ error ជាក់លាក់។ |
| Whisper | អាចទទួល audio file ខូច/ទទេ | Whisper ត្រូវបានហៅតែបន្ទាប់ពី FFmpeg បង្កើត audio 16 kHz mono ដែលមានទំហំគ្រប់គ្រាន់។ |
| Gemini JSON | Code fence អាចមិនត្រូវបានដកត្រឹមត្រូវ | JSON fence parsing ត្រូវបានកែ និង JSON-mode របស់ Gemini នៅតែសកម្ម។ |
| Gemini video context | ការរៀបចំវីដេអូដោយ Gemini អាចរង់ចាំយូរ | កំណត់ finite wait 180 វិនាទី សម្រាប់មុខងារ “កែ SRT” និងបង្ហាញសារ Khmer បើលើសពេល។ |
| API key/data | ការកែលម្អថ្មីអាចប៉ះពាល់សោដែលបានរក្សាទុក | មិនមានការផ្លាស់ប្តូរលើ database schema ឬ UI API key; encrypted-key compatibility ពី v6.4.2 នៅដដែល។ |

## អ្វីដែលបានសាកល្បង

| សាកល្បង | លទ្ធផល |
|---|---|
| Python syntax | Passed |
| Gemini retry/JSON/key fallback simulation | Passed ដោយមិនប្រើ API key របស់អ្នក |
| Khmer SRT, voice-tag និង language validation | Passed |
| Video upload suffix និង partial-file handling | Passed |
| MP4 test clip → FFmpeg → 16 kHz mono audio | Passed |
| Fenced JSON array parsing | Passed |
| Fresh Streamlit startup និង UI login ដើម | Passed |

> ការសាកល្បង Gemini ពិតប្រាកដជាមួយ API key របស់អ្នកមិនត្រូវបានធ្វើទេ ដើម្បីកុំប្រើ quota ឬប៉ះពាល់សោផ្ទាល់ខ្លួនរបស់អ្នក។ កូដបានសាកល្បងតាម mock scenario សម្រាប់ quota, invalid key, transient server error និង JSON-mode។

## របៀប update ដោយរក្សាទិន្នន័យ

សូមជំនួស `app.py`, `requirements.txt`, និង `packages.txt` ក្នុង GitHub repository ដដែល។ **កុំលុប** database, repository ឬ Streamlit Cloud Secrets។ Commit ការផ្លាស់ប្តូរ រួចចុច **Manage app → Reboot app**។ បន្ទាប់ពី Reboot សូមចូល **Manage app → Cloud logs** ហើយមើលថាមិនមាន `Traceback` ឬ `ERROR` ថ្មី។

## កម្រិតជាក់ស្តែង

ការកែលម្អនេះធ្វើឱ្យការបរាជ័យមានសារច្បាស់ និងមិនទុក file បណ្ដោះអាសន្ន ប៉ុន្តែមិនអាចធានាថាសេវាខាងក្រៅដូចជា Gemini, Edge TTS ឬអ៊ីនធឺណិត 4G មិនមាន downtime បានទេ។ ក្នុងករណី Gemini quota ពេញ កម្មវិធីគួរបន្តផ្តល់ Source SRT ពី Whisper ជំនួសការគាំង។
