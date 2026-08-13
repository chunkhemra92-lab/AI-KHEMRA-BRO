# AI KHEMRA BRO v6.4.6 — បញ្ជីតេស្ត Streamlit Cloud

កំណែនេះផ្តោតលើសំឡេងនិយាយធម្មជាតិ និងភាពដាច់ដោយឡែករបស់អ្នកប្រើ។ `[M_THINK]` និង `[F_THINK]` លែងប្រើ echo ទៀតហើយ ដូច្នេះវាគួរស្តាប់ស្រាល និងជិតស្និទ្ធជាងសន្ទនាធម្មតា មិនដូចសំឡេងក្នុងពាង។ សម្លេងធម្មតាត្រូវបានបន្ថយការឡើងចុះខ្លាំងដោយគ្រប់គ្រង loudness range ឱ្យតូចជាងមុន។

## 1. ដាក់កំណែថ្មី

ក្នុង GitHub repository ដដែល សូមជំនួសតែ `app.py`, `requirements.txt`, និង `packages.txt` ពី ZIP v6.4.6។ Commit ការផ្លាស់ប្ដូរ ហើយរង់ចាំ Streamlit Cloud deploy ចប់។ កុំលុប database ឬ App settings ដែលមានស្រាប់។

## 2. ពិនិត្យ Secrets មុន Reboot

ចូល Streamlit Cloud ជាម្ចាស់ app → **Manage app → ⋮ → Settings → Secrets**។ តម្លៃ `COOKIE_SECRET` និង `LICENSE_PEPPER` ត្រូវនៅដដែល ដើម្បីឱ្យ cookies និង access-code hashes ចាស់នៅអាចអានបាន។ Streamlit Cloud គ្រប់គ្រង app secrets នៅ Settings និង app អានវាតាម `st.secrets`។ [1] [2]

```toml
COOKIE_SECRET = "YOUR_EXISTING_LONG_SECRET_DO_NOT_CHANGE"
LICENSE_PEPPER = "YOUR_EXISTING_LONG_SECRET_DO_NOT_CHANGE"
ADMIN_USERNAME = "YOUR_PRIVATE_ADMIN_USERNAME"
ADMIN_PASSWORD = "YOUR_PRIVATE_ADMIN_PASSWORD"

# ជាជម្រើស៖ API fallback របស់ OWNER សម្រាប់ app ទាំងមូល។
# កុំប្រើបើអ្នកចង់ឱ្យគ្រប់ Customer ប្រើ API key ផ្ទាល់ខ្លួនតែប៉ុណ្ណោះ។
GEMINI_API_KEYS = """
AIzaSyOwnerFallbackKeyReplaceThis
"""
```

> `GEMINI_API_KEYS` គឺជា **shared owner fallback**។ វាមិនមែនជា API key ឯកជនរបស់ Customer ម្នាក់ទេ។ ប្រសិនបើគោលការណ៍របស់អ្នកគឺអ្នកប្រើ 1,000 នាក់រៀងៗខ្លួនប្រើសោផ្ទាល់ខ្លួន សូមទុក `GEMINI_API_KEYS` ទទេ ហើយឱ្យពួកគេរក្សាសោនៅក្នុង browser របស់ខ្លួន។ កុំដាក់ API key ឬ secrets ក្នុង GitHub ឬក្នុង chat។

## 3. Reboot និង Logs

ចុច **Manage app → ⋮ → Reboot app**។ រង់ចាំរហូត app បើកទំព័រ login បាន។ បន្ទាប់មកចូល **Manage app → Cloud logs** ហើយស្វែងរក `Traceback`, `ERROR`, `ModuleNotFoundError`, `raw_cookie_secret`, ឬ `Exception`។ ប្រសិនបើគ្មានសារទាំងនេះក្រោយ load និង test យ៉ាងហោចណាស់ម្តង នោះ startup បានជោគជ័យ។ អ្នកអាចទាញយក log តាម menu ក្នុង App management ផងដែរ។ [3]

## 4. តេស្តសំឡេង

ចូលដោយ Access Code សាកល្បង ហើយទៅផ្ទាំង **SRT → Speech**។ សាកល្បង SRT ខាងក្រោម និងចុច Generate MP3។

```srt
1
00:00:00,000 --> 00:00:03,200
[M] ខ្ញុំសូមគិតមើលសិនណា។

2
00:00:03,500 --> 00:00:06,700
[M_THINK] ខ្ញុំសូមគិតមើលសិនណា។

3
00:00:07,000 --> 00:00:10,200
[F] ឯងចង់និយាយអី ប្រាប់មកចុះ។

4
00:00:10,500 --> 00:00:13,700
[F_THINK] ខ្ញុំមិនគួរឱ្យគេដឹងរឿងនេះទេ។
```

| ស្លាក | លទ្ធផលដែលគួរស្តាប់បាន |
|---|---|
| `[M]` / `[F]` | សន្ទនាធម្មតា កក់ក្តៅ មិនលាន់ខ្លាំង ឬធ្លាក់ខ្លាំង។ |
| `[M_THINK]` / `[F_THINK]` | ស្រាល និងទន់ជាងសន្ទនា ប៉ុន្តែ **មិនមាន echo/reverb** និងមិនដូចនិយាយក្នុងពាង។ |

## 5. តេស្តវីដេអូ និង Gemini

ប្រើវីដេអូខ្លី 15–30 វិនាទីដែលសំឡេងច្បាស់។ ជ្រើស `Khmer SRT + MP3 តែម្តង` ហើយជ្រើស `⚡ លឿន`។ ពិនិត្យថា SRT ចេញជាខ្មែរ មានតែ `[M]`, `[F]`, `[M_THINK]`, `[F_THINK]` និង MP3 អាចស្តាប់/ទាញយកបាន។ បើ Gemini quota ពេញ អ្នកគួរឃើញសារជាក់លាក់អំពី quota មិនមែន app គាំង។

## 6. តេស្តភាពដាច់ដោយឡែករបស់អ្នកប្រើ

សម្រាប់សាកល្បងការដាច់ទិន្នន័យ សូមបង្កើត **Access Code ពីរផ្សេងគ្នា** ក្នុង Admin dashboard។ បើក browser ធម្មតាសម្រាប់ Code A និង Incognito ឬ browser ផ្សេងសម្រាប់ Code B។ នៅ Code A បញ្ចូល SRT ឬវីដេអូខ្លី ហើយរក្សា API key test មួយ។ នៅ Code B អ្នកមិនត្រូវឃើញ SRT, MP3, preview, workspace ឬ API key ពី Code A ទេ។ បន្ទាប់មក logout Code A ក្នុង browser ដដែល ហើយ login Code B; ទិន្នន័យបណ្ដោះអាសន្នចាស់ត្រូវបានសម្អាតមុនបង្កើត workspace ថ្មី។

> Code នីមួយៗគួរចែកឱ្យអ្នកប្រើម្នាក់។ កូដអាចចូលបានពីទូរស័ព្ទ/Browser ច្រើន ប៉ុន្តែប្រសិនបើមនុស្សច្រើនចែកប្រើ **កូដដូចគ្នា** វាមិនមែនជាការបែងចែកគណនីពេញលេញទេ។ ដើម្បីបែងចែកអ្នកប្រើ 1,000 នាក់ ត្រូវបង្កើត Access Code ដាច់ដោយឡែក 1,000 កូដ។

## 7. កម្រិតសមត្ថភាពដែលត្រូវយល់

កូដ v6.4.6 បំបែក temporary workspace និង personal browser API key ដោយដាច់ពីគ្នា។ ទោះជាយ៉ាងណា **Streamlit Community Cloud + local SQLite + CPU Whisper មិនអាចធានាការដំណើរការវីដេអូ 1,000 នាក់ក្នុងពេលតែមួយបានទេ**។ សម្រាប់ចំនួនអ្នកប្រើធំ ត្រូវប្រើ database ដែលមាន persistence, object storage សម្រាប់វីដេអូ និង job queue/compute ដែលអាចពង្រីកបាន។ នេះជាបញ្ហាសមត្ថភាពប្រព័ន្ធ មិនមែនបញ្ហា UI ឬ Access Code ទេ។

## References

[1] [Streamlit Docs — Secrets management for Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)

[2] [Streamlit Docs — Secrets management](https://docs.streamlit.io/develop/concepts/connections/secrets-management)

[3] [Streamlit Docs — Manage your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)
