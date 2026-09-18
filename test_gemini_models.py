from pathlib import Path

SOURCE = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

assert '"gemini-3.8-flash"' in SOURCE
assert 'DEFAULT_GEMINI_TRANSLATION_MODEL = "gemini-3.8-flash"' in SOURCE
assert '"gemini-3.8-flash": "🚀 Gemini 3.8 Flash — ថ្មីបំផុត និងណែនាំ"' in SOURCE
assert 'def _candidate_gemini_models(selected_model):' in SOURCE
assert 'GEMINI_TRANSLATION_MODEL_OPTIONS' in SOURCE
print("Gemini 3.8 Flash model selection assertions passed")
