# AI KHEMRA BRO v6.4.1 — Gemini API Hardening

កំណែនេះជាការកែលម្អលើ v6.4 ដែលផ្តោតលើ **ភាពធន់របស់ Gemini API**, ការរក្សាសោ API ដែលមានស្រាប់ និងការបន្តប្រើ UI ដើម។ វាមិនបន្ថែមផ្ទាំងធំ ឬជំហានការងារថ្មីទៅក្នុង workspace ទេ។ លំហូរលឿនសម្រាប់វីដេអូ និង Auto SRT/MP3 នៅដដែល។

## ការកែលម្អសំខាន់

| ផ្នែក | ការកែលម្អក្នុង v6.4.1 |
|---|---|
| JSON response | ការហៅ Gemini កំណត់ `application/json` ដើម្បីបន្ថយបញ្ហា output មិនមែន JSON និងធ្វើឱ្យ SRT parse មានស្ថិរភាព។ |
| Retry | Retry បន្ថែមត្រូវបានកំណត់ត្រឹមម្តង សម្រាប់តែ 5xx/network timeout។ កំហុស quota និង API key មិនត្រូវបានរង់ចាំ retry ច្រើនដងទេ។ |
| Model fallback | ប្រើបញ្ជីខ្លីនៃ stable models: selected model, `gemini-3.5-flash-lite`, `gemini-3.6-flash`, និង `gemini-2.5-flash-lite`។ |
| API key fallback | បើ API key មិនត្រឹមត្រូវ ឬត្រូវ block កម្មវិធីរំលងទៅសោបន្ទាប់ភ្លាម។ បើ model មិនមាន ឬសេវាផ្អាក វាសាក model បន្ទាប់ដោយស្វ័យប្រវត្តិ។ |
| ការរក្សាសោ | Key ដែលបានអ៊ិនគ្រីបពី v6.4 នៅតែអាចអានបាន។ ប្រសិនបើកំណត់ `COOKIE_SECRET` ថ្មី ការរក្សាទុកថ្មីប្រើសោថ្មី ប៉ុន្តែការអានសោចាស់នៅតែដំណើរការ។ |
| ការរក្សាទុកបរាជ័យ | កម្មវិធីមិនបង្ហាញថា API key បានរក្សាទុកជោគជ័យទេ បើ database update បរាជ័យ។ សោចាស់មិនត្រូវបានលុប។ |
| សារ error | Error ដែលបង្ហាញលើ UI លាក់ URL និងអត្ថបទដែលមានទម្រង់ដូច API key។ |
| UI និងវីដេអូ | Login, menu, tabs និងលំហូរវីដេអូដើមត្រូវបានរក្សាទុក។ របៀបលឿននៅតែទាញ audio ដោយផ្ទាល់សម្រាប់ Whisper។ |

## សំខាន់អំពី Gemini quota

> Rate limit របស់ Gemini ត្រូវបានគណនាតាម **Google Cloud project** មិនមែនតាម API key ដាច់ដោយឡែកទេ។ ដូច្នេះបើសោច្រើនស្ថិតនៅក្នុង project ដូចគ្នា ការប្តូរសោអាចមិនដោះស្រាយ quota បានទេ។ កម្មវិធីរក្សា key fallback សម្រាប់សោពី project ផ្សេង ឬសោដែលមានស្ថានភាពខុសគ្នា។ [1]

Gemini SDK មាន retry សម្រាប់កំហុសបណ្ដោះអាសន្នរួចហើយ។ កំណែនេះបន្ថែមតែ retry ដែលមានដែនកំណត់ និង jitter ដើម្បីមិនធ្វើឱ្យការរង់ចាំយូរ នៅពេល quota ពេញ។ [2]

## របៀប update ដោយមិនបាត់ API key

សូមជំនួសតែ `app.py`, `requirements.txt`, និង `packages.txt` ក្នុង GitHub repository ដដែល។ កុំលុប database ឬ Streamlit secrets ដែលមានស្រាប់។ Commit រួចហើយ ចុច **Manage app → Reboot app** នៅ Streamlit Cloud។ API key ដែលអ្នកបានរក្សាទុកក្នុងគណនីពីមុនត្រូវបន្តមាន ប្រសិនបើ database របស់ deployment ដដែលត្រូវបានរក្សាទុក។

សម្រាប់ការការពារបន្ថែម អ្នកអាចដាក់ `COOKIE_SECRET` ជាតម្លៃវែង និងសម្ងាត់ក្នុង Streamlit Cloud **Secrets**។ កំណែនេះរក្សាសមត្ថភាពអាន key ដែលបានអ៊ិនគ្រីបពីមុន ដូច្នេះការបន្ថែម Secret មិនគួរធ្វើឱ្យ API key ចាស់បាត់។ កុំដាក់ Gemini API key ដោយផ្ទាល់ក្នុង `app.py`, `README.md`, ឬ GitHub repository សាធារណៈ។

## តេស្តរហ័សលើទូរស័ព្ទ

បើកកម្មវិធី បញ្ចូល Access Code របស់អ្នក ហើយបើកម៉ឺនុយ **☰**។ ត្រូវឃើញ API key ដែលរក្សាទុកពីមុនក្នុងប្រអប់ Key ហើយអាចបន្តប្រើបាន។ សាកល្បង SRT ខ្លី 3–5 បន្ទាត់មុន។ បើ Gemini quota ពេញ កម្មវិធីគួរបង្ហាញសារច្បាស់ថា quota ពេញ ជំនួសឱ្យទុក SRT ចិនបំភាន់ថាជា Khmer SRT។

## References

[1] [Google AI for Developers — Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)

[2] [Google AI for Developers — Gemini API troubleshooting and retry strategy](https://ai.google.dev/gemini-api/docs/troubleshooting)
