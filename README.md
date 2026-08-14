# AI KHEMRA BRO v6.6.3

កម្មវិធី Streamlit សម្រាប់ទាញសំឡេងពីវីដេអូ បង្កើត SRT បកប្រែចិន/កូរ៉េ/វៀតណាម/អង់គ្លេសទៅខ្មែរ និងបង្កើតសំឡេង Khmer MP3 ជាមួយ tag `[M]`, `[F]`, `[M_THINK]`, `[F_THINK]`។

## ឯកសារត្រូវ Upload ទៅ Streamlit Cloud

| ឯកសារ | តួនាទី |
|---|---|
| `app.py` | កម្មវិធីទាំងមូល និង UI សម្រាប់ទូរស័ព្ទ |
| `requirements.txt` | Python dependencies ដែល Streamlit Cloud ត្រូវដំឡើង |
| `packages.txt` | System dependency: `ffmpeg` |
| `.gitignore` | ការពារ API key, license database និង temporary files មិនឱ្យចូល Git |

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

ដាក់ឯកសារ 4 ខាងលើនៅ root នៃ GitHub repository រួចភ្ជាប់ repository ទៅ Streamlit Community Cloud។ កំណត់ `app.py` ជា main file ហើយបញ្ចូល Secrets មុនចុច Reboot។

## ការប្រើ Settings

ចុច `☰` នៅផ្នែកខាងលើ រួចជ្រើស Gemini Model និង Translation Style។ `Standard` សមស្របសម្រាប់ការបកប្រែទូទៅ ខណៈ `Lipsync` សរសេរឃ្លាខ្លីស៊ី timing សម្រាប់ dubbing។ ការកំណត់នេះអនុវត្តទៅទាំង Video → SRT និង AI Subtitle Translator។

## មិនត្រូវ Upload

កុំ Upload `licenses.db`, `.streamlit/secrets.toml`, វីដេអូផ្ទាល់ខ្លួន, MP3, ឬ API key ទៅ GitHub។ `.gitignore` បានបញ្ជាក់ការការពារឯកសារទាំងនេះរួច។
