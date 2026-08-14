# AI KHEMRA BRO v6.6.5

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

## មិនត្រូវ Upload

កុំ Upload `licenses.db`, `.streamlit/secrets.toml`, វីដេអូផ្ទាល់ខ្លួន, MP3, ឬ API key ទៅ GitHub។ `.gitignore` បានបញ្ជាក់ការការពារឯកសារទាំងនេះរួច។
