# AI KHEMRA BRO v6.4.5 — សំឡេង និង Streamlit Secrets

កំណែនេះកែលម្អបែបសំឡេងដោយមិនប្តូរ UI ដើម។ សន្ទនា `[M]` និង `[F]` ត្រូវបានកែឱ្យមានសម្លេងកក់ក្តៅ និងកាត់បន្ថយប្រេកង់ខ្ពស់ដែលធ្វើឱ្យសម្លេងខ្យល់។ ស្លាក `[M_THINK]` និង `[F_THINK]` ត្រូវបានបន្ថយល្បឿន កម្ពស់សម្លេង និងកម្រិតសំឡេង ហើយបន្ថែម echo ស្រាល ដើម្បីឱ្យស្តាប់ដូចជាសំឡេងគិតក្នុងចិត្ត មិនដូចសន្ទនាធម្មតា។

Prompt ដែលកម្មវិធីប្រើសម្រាប់បកប្រែសកម្ម ត្រូវបានរឹតបន្តឹងតាមច្បាប់ទាំង ៦ របស់អ្នក។ វាបញ្ជាក់ឱ្យប្រើភាសានិយាយខ្មែរ មិនបកប្រែត្រង់ពេក, រក្សាអារម្មណ៍ និងសព្វនាមតាមតួអង្គ, រក្សា timing, ប្រើតែស្លាក 4 ប្រភេទ និងប្រើ `THINK` តែសម្រាប់គំនិតក្នុងចិត្តពិតប្រាកដ។ Rule 6 បន្ថែម Facebook-safe language ដោយរក្សាអារម្មណ៍ឈុតឆាក ប៉ុន្តែបម្លែងពាក្យអាសអាភាស ការប្រមាថ និងការរើសអើងទៅជាពាក្យខ្មែរសមរម្យ។

## កំណត់ Streamlit Secrets លើទូរស័ព្ទ

បើក app របស់អ្នកក្នុង browser ហើយចូលគណនី Streamlit ដែលជាម្ចាស់ app។ ចុច **Manage app** ខាងស្តាំក្រោម → ចុច **⋮** → **Settings** → ផ្ទាំង **Secrets**។ បញ្ចូល TOML ខាងក្រោមក្នុងប្រអប់ Secrets រួចចុច **Save**។ បន្ទាប់ពី Save សូមចុច **Reboot app** ម្តង ដើម្បីឱ្យការកំណត់ថ្មីចូលដំណើរការ។ Streamlit Community Cloud ផ្តល់ការគ្រប់គ្រង secrets តាម App settings ហើយ code អាចអានតម្លៃទាំងនេះតាម `st.secrets`។ [1] [2]

```toml
# រក្សាតម្លៃនេះឱ្យដដែលជានិច្ច។ កុំប្តូរ វេលា Reboot ឬ update app។
COOKIE_SECRET = "PUT_A_LONG_UNIQUE_RANDOM_SECRET_HERE"

# API key server-side fallback។ បញ្ចូលមួយ key ក្នុងមួយបន្ទាត់។
# កុំដាក់ key នេះក្នុង app.py ឬ GitHub repository។
GEMINI_API_KEYS = """
AIzaSyExampleKeyOneReplaceThis
AIzaSyExampleKeyTwoReplaceThis
"""

# ជាជម្រើស៖ ការពារ license/admin hashing និង login settings។
LICENSE_PEPPER = "PUT_ANOTHER_LONG_UNIQUE_RANDOM_SECRET_HERE"
ADMIN_USERNAME = "KHEMRA"
ADMIN_PASSWORD = "CHOOSE_A_STRONG_PRIVATE_PASSWORD"
```

> តម្លៃខាងលើគ្រាន់តែជាគំរូប៉ុណ្ណោះ។ សូមបង្កើត `COOKIE_SECRET`, `LICENSE_PEPPER` និង `ADMIN_PASSWORD` ផ្ទាល់ខ្លួន ហើយកុំផ្ញើវាមកក្នុង chat ឬដាក់ក្នុង GitHub។

## របៀបដែល API key ត្រូវបានរក្សា

| ប្រភពសោ | គោលបំណង | ធន់ពេល Reboot |
|---|---|---|
| Customer account / browser cookie | សោផ្ទាល់ខ្លួនដែលអ្នករក្សាទុកក្នុងម៉ឺនុយ ☰ | អាចស្ដារបាន ដរាបណា cookie ឬ database នៅមាន និង `COOKIE_SECRET` មិនត្រូវបានប្តូរ។ |
| `GEMINI_API_KEYS` ក្នុង Secrets | fallback សម្រាប់ app ទាំងមូល ដោយមិនបង្ហាញនៅ UI | បន្តប្រើក្រោយ Reboot/deploy ដរាបណា Secrets ដដែលនៅ App settings។ |
| `COOKIE_SECRET` | សោសម្រាប់អ៊ិនគ្រីប/អាន key ដែលបានរក្សាទុក | ត្រូវរក្សាតម្លៃដដែល; ការប្តូរតម្លៃអាចធ្វើឱ្យ key ថ្មីៗមិនអាចអានបាន។ |

**ចំណាំសំខាន់៖** Streamlit Secrets រក្សា configuration របស់ app ប៉ុន្តែមិនមែនជាឃ្លាំង database សម្រាប់ user API key ម្នាក់ៗទេ។ `GEMINI_API_KEYS` ជា fallback ដែលជួយឱ្យ app នៅតែបកប្រែបាន ប្រសិនបើ local SQLite storage ត្រូវបានកំណត់ឡើងវិញ។ ប្រសិនបើអ្នកចង់រក្សា key ផ្ទាល់ខ្លួនរបស់អ្នកប្រើម្នាក់ៗដោយធន់ពេញលេញលើ deployment, គួរប្រើ database ខាងក្រៅដែលមាន persistence ជាក់លាក់។

## តេស្តក្រោយ Reboot

បន្ទាប់ពី Reboot សូមចូល app → Upload វីដេអូខ្លី → ជ្រើស `Khmer SRT + MP3 តែម្តង`។ ពិនិត្យ SRT ថាប្រើ `[M]`, `[F]`, `[M_THINK]`, ឬ `[F_THINK]` តែប៉ុណ្ណោះ។ សម្រាប់តេស្តសំឡេងគិតក្នុងចិត្ត សូមប្រើ SRT ខ្លីដែលមាន `[M_THINK] ខ្ញុំមិនអាចឱ្យគេដឹងរឿងនេះទេ។` ហើយប្រៀបធៀបជាមួយ `[M] ខ្ញុំមិនអាចឱ្យគេដឹងរឿងនេះទេ។` សម្លេងគិតក្នុងចិត្តត្រូវស្តាប់ស្រាល ទាប និងមាន echo តិចជាងសន្ទនាធម្មតា។

## References

[1] [Streamlit Docs — Secrets management for Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)

[2] [Streamlit Docs — App settings and Secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-settings)
