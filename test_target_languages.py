from pathlib import Path
import re

SOURCE = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

EXPECTED = {
    '"🇨🇳 中文 (Chinese)"': '"code": "zh"',
    '"🇺🇸 English (US)"': '"code": "en"',
    '"🇻🇳 Tiếng Việt"': '"code": "vi"',
    '"🇯🇵 日本語"': '"code": "ja"',
    '"🇮🇩 Bahasa Indonesia"': '"code": "id"',
    '"🇰🇷 한국어 (Korean)"': '"code": "ko"',
}

for label, code in EXPECTED.items():
    assert label in SOURCE, f"missing target language label: {label}"
    start = SOURCE.index(label)
    window = SOURCE[start:start + 100]
    assert code in window, f"wrong mapping for {label}"

assert 'def google_translate_texts(texts, google_api_key, target_code="km")' in SOURCE
assert '"target": target_code' in SOURCE
assert 'google_translate_texts(sources, google_api_key, target_code)' in SOURCE
assert re.search(r'target_code\s*=\s*target_language_details\(target_language\)\["code"\]', SOURCE)
print("target-language registry and Google target forwarding passed")
