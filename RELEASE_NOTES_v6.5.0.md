# AI KHEMRA BRO v6.5.0 — Full Natural Audio Processing

កំណែ v6.5.0 កែលម្អ **audio pipeline ពិតក្នុង `app.py`** សម្រាប់ Video → SRT → MP3, SRT → Speech និង Text → Speech។ វាមិនមែនជាការកែ test ឬឯកសារណែនាំតែប៉ុណ្ណោះទេ។

## ការកែលម្អសំខាន់ៗ

| ផ្នែក | ការកែលម្អ |
|---|---|
| កម្រិតសំឡេងរវាង cue | បន្ថែម slow final leveler ដែលប្រើ frame 800 ms, 75% overlap និងកំណត់ gain អតិបរមា 1.25× ដើម្បីសម្រួល cue-to-cue loudness ដោយមិន pump តាមព្យាង្គ។ |
| សំឡេងប្រុស/ស្រី | កែ speaker alignment ដោយបន្ថយ `[F]` បន្តិច ដើម្បីកាត់បន្ថយភាពខុសកម្រិតរវាងសំឡេងប្រុស និងស្រី។ |
| Thought voices | `[M_THINK]` និង `[F_THINK]` ទន់ជាង dialogue, គ្មាន echo និងប្រើ EQ ទន់ៗ; មិនស្តាប់ដូចនិយាយក្នុងពាង។ |
| SRT/Video dubbing | រក្សា fade-in 0.018s, fade-out 0.030s, គ្មាន forced gap និង tempo អតិបរមា 1.10×។ |
| Text → Speech | ឥឡូវប្រើ cleanup, gentle compression, final leveler, limiter និង loudness mastering ដូចគ្នានឹង SRT/Video workflow។ |
| In-app help | មាន guide ពង្រីកបានសម្រាប់ `[M_THINK]` និង `[F_THINK]` ទាំងក្នុង SRT → Speech និង Text → Speech។ |

## ការផ្ទៀងផ្ទាត់

Regression tests ទាំង 7 suites និង Python compilation បានឆ្លងកាត់។ Live Edge TTS test បានបង្កើត normal voice, thought voice និង polished Text → Speech MP3 ជោគជ័យ។ UI ក្នុង browser ក៏ត្រូវបានពិនិត្យជាក់ស្តែងថា guide, tag cards និង v6.5.0 footer បង្ហាញបានត្រឹមត្រូវ។

> គុណភាពធម្មជាតិអាស្រ័យលើ Edge TTS និងអត្ថបទ SRT ផងដែរ។ សូមប្រើ cue ខ្លី រលូន មានវណ្ណយុត្តិ និងទុកពេលគ្រប់គ្រាន់សម្រាប់ឃ្លានីមួយៗ។

## Deploy ទៅ Streamlit Community Cloud

ដាក់ជំនួស `app.py`, `requirements.txt` និង `packages.txt` ក្នុង repository របស់អ្នក រួច reboot app។ កុំដាក់ `licenses.db`, local test files ឬ API key ក្នុង Git repository។ រក្សា Streamlit Secrets ដដែល៖ `COOKIE_SECRET`, `GEMINI_API_KEYS`, `LICENSE_PEPPER` និង `ADMIN_PASSWORD`។ បើចាំបាច់ប្តូរ `COOKIE_SECRET`, រក្សាសោចាស់ក្នុង `PREVIOUS_COOKIE_SECRETS` ដើម្បីអាន API key cookie ចាស់បាន។
