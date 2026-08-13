# ជួសជុល `ModuleNotFoundError: edge_tts` នៅ Streamlit Cloud

កំហុសក្នុងរូបភាពបង្ហាញថា Streamlit Cloud បានដំណើរការ `app.py` ប៉ុន្តែមិនបានដំឡើងកញ្ចប់ Python `edge-tts`។ កំណែជួសជុលនេះមាន `requirements.txt` ដែលបានកំណត់កំណែ package ជាក់លាក់ និងបានសាកល្បងចាប់ផ្ដើមកម្មវិធីរួចហើយ។

> សូមដាក់ **`app.py`**, **`requirements.txt`**, និង **`packages.txt`** នៅក្នុងថតដូចគ្នា ក្នុង root នៃ GitHub repository ដែលមាន `app.py`។ កុំ upload តែ `app.py` មួយឯកសារ។

## ជំហាន redeploy

| លំដាប់ | អ្វីដែលត្រូវធ្វើ |
|---|---|
| 1 | ទាញយក និងពន្លា ZIP កំណែជួសជុល។ |
| 2 | ចូល GitHub repository `ai-khemra-bro` របស់អ្នក ហើយបើកថតដែលមាន `app.py`។ |
| 3 | ជំនួសឯកសារ `app.py`, `requirements.txt`, និង `packages.txt` ដោយឯកសារពី ZIP នេះ។ |
| 4 | ផ្ទៀងផ្ទាត់ថា `requirements.txt` មានបន្ទាត់ `edge-tts==7.2.8`។ |
| 5 | Commit ការផ្លាស់ប្តូរទៅ branch ដែល Streamlit Cloud កំពុង deploy។ |
| 6 | នៅ Streamlit Cloud ចុច **Manage app** → **Reboot app** ដើម្បីឱ្យវាដំឡើង dependencies ថ្មីឡើងវិញ។ |
| 7 | បើមានជម្រើស Python version សូមជ្រើស **Python 3.12** ដើម្បីឱ្យដូចបរិស្ថានដែលបានផ្ទៀងផ្ទាត់។ |

## ផ្ទៀងផ្ទាត់មុន reboot

ឯកសារ `requirements.txt` ត្រូវស្ថិតនៅ **repository root** ឬក្នុងថតដូចគ្នានឹង `app.py`។ ប្រសិនបើ repository របស់អ្នកមាន `uv.lock`, `Pipfile`, `environment.yml`, ឬ `pyproject.toml` សម្រាប់ dependency រួចហើយ សូមកុំទុកឯកសារទាំងនោះឱ្យប៉ះទង្គិចជាមួយ `requirements.txt`; Streamlit Cloud អាចជ្រើសយក dependency file ផ្សេងមុន `requirements.txt`។

| ឯកសារ | មុខងារ |
|---|---|
| `requirements.txt` | ដំឡើង Python packages រួមទាំង `edge-tts`។ |
| `packages.txt` | ដំឡើង `ffmpeg` នៅ Linux សម្រាប់ដំណើរការវីដេអូ និងសំឡេង។ |
| `app.py` | កូដកម្មវិធី។ |

បន្ទាប់ពី reboot រួច ទំព័រ login គួរតែបើកឡើងជំនួសឱ្យ `ModuleNotFoundError`។ ប្រសិនបើកំហុសនៅតែមាន សូមបើក **Manage app** → **Logs** ហើយផ្ញើរូបភាពនៃផ្នែក log ថ្មីមកខ្ញុំ។

## ប្រភពផ្លូវការ

[1]: https://docs.streamlit.io/knowledge-base/dependencies/module-not-found-error "Streamlit: ModuleNotFoundError"
[2]: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies "Streamlit: Community Cloud app dependencies"

[1] Streamlit បញ្ជាក់ថា `ModuleNotFoundError` លើ Community Cloud កើតឡើងនៅពេល package ដែល import មិនត្រូវបានដាក់ក្នុង requirements file។

[2] Streamlit បញ្ជាក់ថា `requirements.txt` គួរដាក់នៅ repository root ឬក្នុងថតដូចគ្នានឹង entrypoint និងថា Community Cloud អាចជ្រើស dependency file ផ្សេងមុន ដោយយោងតាមលំដាប់អាទិភាព។
