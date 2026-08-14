# AI KHEMRA BRO v6.6.8

កម្មវិធី Streamlit សម្រាប់ទាញសំឡេងពីវីដេអូ បង្កើត SRT និង dubbing MP3។ អ្នកប្រើប្រាស់ម្នាក់ៗអាចជ្រើសភាសាគោលដៅដោយខ្លួនឯង៖ **Khmer (ខ្មែរ), English, Chinese (中文), Korean (한국어)** ឬ **Vietnamese (Tiếng Việt)**។ សំឡេង MP3 ប្រើ male/female voice ដែលត្រូវនឹងភាសាគោលដៅ និង tag `[M]`, `[F]`, `[M_THINK]`, `[F_THINK]`។

## ឯកសារត្រូវ Upload ទៅ Streamlit Cloud

| ឯកសារ | តួនាទី |
|---|---|
| `app.py` | កម្មវិធីទាំងមូល និង UI សម្រាប់ទូរស័ព្ទ |
| `requirements.txt` | Python dependencies ដែល Streamlit Cloud ត្រូវដំឡើង |
| `packages.txt` | System dependency: `ffmpeg` |
| `.gitignore` | ការពារ API key, license database និង temporary files មិនឱ្យចូល Git |
| `README.md` | សេចក្តីណែនាំ deploy និងការជ្រើសភាសាគោលដៅ |

## Streamlit Secrets

បង្កើត Secrets នៅក្នុង Streamlit Cloud ដូចខាងក្រោម។ កុំដាក់ API key ក្នុង `app.py`, GitHub ឬ README។

```toml
COOKIE_SECRET = "បង្កើត-secret-វែង-និង-ពិបាកទាយ"
GEMINI_API_KEYS = "AIza..."
LICENSE_PEPPER = "secret-ផ្សេង-សម្រាប់-access-code"
ADMIN_PASSWORD = "password-របស់-owner"
ADMIN_USERNAME = "KHEMRA"

# ប្រើតែពេលអ្នកប្តូរ COOKIE_SECRET ដើម្បីអាន key ចាស់បាន
# PREVIOUS_COOKIE_SECRETS = "COOKIE_SECRET_ចាស់"
```

## ដាក់ដំណើរការ

ដាក់ឯកសារ 5 ខាងលើនៅ root នៃ GitHub repository រួចភ្ជាប់ repository ទៅ Streamlit Community Cloud។ កំណត់ `app.py` ជា main file ហើយបញ្ចូល Secrets មុនចុច Reboot។

## ការប្រើ Settings

ចុច `☰` នៅផ្នែកខាងលើ រួចជ្រើស **Gemini Model**, **Target Language** និង **Translation Style**។ អ្នកអាចជ្រើស Khmer, English, Chinese, Korean ឬ Vietnamese សម្រាប់ទាំង Video → SRT, AI Subtitle Translator, SRT → Speech និង Text → Speech។ `Standard` សមស្របសម្រាប់ការបកប្រែទូទៅ ខណៈ `Lipsync` សរសេរឃ្លាខ្លីស៊ី timing សម្រាប់ dubbing។

ជម្រើស Target Language, Model និង Translation Style ត្រូវបានអ៊ិនគ្រីប និងរក្សាទុកជាឯកជនតាម Access Code របស់អ្នកប្រើម្នាក់ៗ។ ដូច្នេះអ្នកប្រើ A អាចជ្រើស English ខណៈអ្នកប្រើ B ជ្រើស Khmer ដោយមិនប៉ះពាល់គ្នា។

## Video Upload លឿន និងស្រាល

ផ្នែក **Video → SRT** ទទួលវីដេអូ MP4, MOV, MKV ឬ WEBM ដែលមានរយៈពេល **10 នាទីចុះក្រោម** និងទំហំអតិបរមា **100 MB** (`Lite mode` អតិបរមា 60 MB)។ ប្រអប់ upload ត្រូវបានកាត់ឱ្យតូចសមស្របសម្រាប់ទូរស័ព្ទ និងការពារអក្សរមិនឱ្យលេចចេញក្រៅប្រអប់។

សម្រាប់ upload លឿន សូមប្រើ MP4 720p ឬ 480p ដែលតូចជាង 100 MB។ កម្មវិធីរក្សាវីដេអូជាប្លុក 4 MB ហើយទាញតែសំឡេង mono 16 kHz សម្រាប់ ASR ដើម្បីប្រើ memory តិច។ វីដេអូលើស 10 នាទីត្រូវបានបញ្ឈប់មុនចាប់ផ្តើម ASR/Gemini workflow។

## កាតព័ត៌មានគណនី

នៅក្នុង `☰ Settings` កាតព័ត៌មានគណនីបង្ហាញ **ឈ្មោះ**, **Plan**, **លេខកូដ**, **ថ្ងៃ/ម៉ោងផុតកំណត់** និង **ចំនួនថ្ងៃនៅសល់** ក្នុងរចនាប័ទ្មស្អាតសមស្របសម្រាប់ទូរស័ព្ទ។ កាតនេះ refresh ម្តងក្នុងមួយនាទី ដើម្បីមិនឱ្យលេខវិនាទីលោតរញ៉េរញ៉ៃ។ វាបង្ហាញតែព័ត៌មានរបស់ Access Code ដែលបានចូលបច្ចុប្បន្នប៉ុណ្ណោះ។

## Owner Backup និងការពារ Access Code ពេល Update

នៅក្នុង Owner dashboard សូមបើក `🔐 គ្រប់គ្រង API Key និង Backup Access Code` រួចទាញយក **Backup Access Code** មុន update ឬ reboot។ Backup មានឈ្មោះអតិថិជន, Access Code, Plan និងថ្ងៃផុតកំណត់ ប៉ុន្តែ **មិនមាន API Key**។

បើ hosting មិនរក្សា `licenses.db` ចាស់ក្រោយ update សូម Restore Backup នោះ។ Restore នាំចូលតែ Access Code ដែលមិនទាន់មាន ហើយ **មិន overwrite, មិនលុប និងមិនបង្កើតលេខកូដថ្មី** សម្រាប់លេខកូដដែលមានរួចទេ។

> កុំប្តូរ `COOKIE_SECRET` ឬ `LICENSE_PEPPER` ដោយគ្មានការកំណត់ `PREVIOUS_COOKIE_SECRETS`/ការផែនការផ្ទេរទិន្នន័យត្រឹមត្រូវ។ សោទាំងនេះត្រូវរក្សាឱ្យថេរ ដើម្បីអានទិន្នន័យអ៊ិនគ្រីប និងផ្ទៀងផ្ទាត់ Access Code ចាស់បាន។

Owner dashboard បង្ហាញតែស្ថានភាពថា App API Key ពី Streamlit Secrets មានឬអត់ ហើយមិនបង្ហាញតម្លៃសោ។ ដើម្បីប្តូរ App API Key សូមកែ `GEMINI_API_KEYS` ក្នុង Streamlit Secrets ដោយផ្ទាល់។

## មិនត្រូវ Upload

កុំ Upload `licenses.db`, `.streamlit/secrets.toml`, វីដេអូផ្ទាល់ខ្លួន, MP3, ឬ API key ទៅ GitHub។ `.gitignore` បានបញ្ជាក់ការការពារឯកសារទាំងនេះរួច។
