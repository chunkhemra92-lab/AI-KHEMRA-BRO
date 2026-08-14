# AI KHEMRA BRO v6.6.0 — Full Audio Ducking

កំណែ v6.6.0 ដំឡើង **Audio Ducking ពេញលេញ** ក្នុង `app.py`។ អ្នកអាច upload ភ្លេងកំដរ ជ្រើស Auto Ducking និងបង្កើត MP3 ដែលភ្លេងថយចុះស្វ័យប្រវត្តិពេលមានសំឡេងនិយាយ។ មុខងារនេះមាននៅក្នុង **Video → SRT**, **SRT → Speech** និង **Text → Speech**។

## មុខងារថ្មី

| ផ្នែក | ការដំឡើងក្នុង v6.6.0 |
|---|---|
| Music upload | គាំទ្រ MP3, WAV, M4A, AAC និង OGG រហូតដល់ 30 MB ក្នុង workspace ឯកជនរបស់ browser session។ |
| Auto Ducking | ប្រើ FFmpeg `sidechaincompress` ដើម្បីបន្ថយភ្លេងពេលមានសំឡេងនិយាយ និងលាយត្រឡប់ដោយរលូន។ |
| Mobile controls | មាន expander មួយសម្រាប់ music upload, switch Auto Ducking, កម្រិតភ្លេង, កម្លាំង ducking, attack និង release។ |
| Voice quality | រក្សា natural audio cleanup, slow final leveler, limiter និង loudness mastering ពី v6.5.0។ |
| Fallback | បើមិន upload ភ្លេង MP3 នឹងបង្កើតសំឡេងធម្មតាដូច workflow កំណែចាស់។ |
| Privacy | Music tracks, ducking settings និង workspace ត្រូវបានលុបពេល Clear Project, logout ឬប្តូរអតិថិជន។ |

## Default ដែលបានណែនាំ

`Music gain = 0.42`, `Ducking ratio = 8`, `Attack = 40 ms`, និង `Release = 700 ms`។ កំណត់នេះធ្វើឱ្យភ្លេងថយទន់ៗពេលសន្ទនា និងមិនងើបឡើងកន្ត្រាក់រវាងពាក្យ។

> បើភ្លេងងើបឡើងលឿនពេករវាងឃ្លា សូមបង្កើន **ឡើងភ្លេងវិញ (Release)** ទៅ 900 ms មុនពេលបង្កើន Ducking ratio។

## ការផ្ទៀងផ្ទាត់

បានសាកល្បង FFmpeg sidechain ducking ពិតជាមួយ music track, Text → Speech, SRT → MP3, no-music fallback, private music upload, browser-session isolation, full regression suite និងការបើក UI v6.6.0 ក្នុង browser។

## Deploy

ជំនួស `app.py`, `requirements.txt` និង `packages.txt` ក្នុង repository របស់អ្នក រួច reboot app នៅ Streamlit Cloud។ មិនត្រូវ upload `licenses.db`, music test files ឬ API key ទៅ Git repository ទេ។ Streamlit Secrets ដែលមានស្រាប់នៅដដែល៖ `COOKIE_SECRET`, `GEMINI_API_KEYS`, `LICENSE_PEPPER` និង `ADMIN_PASSWORD`។
