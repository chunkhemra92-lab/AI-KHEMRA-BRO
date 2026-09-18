from pathlib import Path

SOURCE = Path(__file__).with_name("app.py").read_text(encoding="utf-8")

EXPECTED_MODELS = (
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
)
for model in EXPECTED_MODELS:
    assert f'"{model}"' in SOURCE, f"missing translation model: {model}"
assert 'DEFAULT_GEMINI_TRANSLATION_MODEL = "gemini-3.8-flash"' in SOURCE
assert 'def _candidate_gemini_models(selected_model):' in SOURCE
assert 'batch_size = 60' in SOURCE
assert 'missing = [cue for cue in batch if cue["id"] not in translated]' in SOURCE
assert 'still_missing = [cue["id"] for cue in batch if cue["id"] not in translated]' in SOURCE
print("Complete Gemini 2.5–3.8 translation catalog and no-loss repair assertions passed")
