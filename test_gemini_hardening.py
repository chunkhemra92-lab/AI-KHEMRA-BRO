import ast
import base64
import hashlib
import random
import time
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from google.genai import types

source_path = Path(__file__).with_name("app.py")
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
needed_assignments = {"LEGACY_COOKIE_SECRET"}
needed_functions = {
    "_clean_api_keys",
    "encrypt_api_keys",
    "decrypt_api_keys",
    "_error_message",
    "is_quota_error",
    "is_invalid_key_error",
    "is_model_unavailable_error",
    "is_transient_gemini_error",
    "is_structured_output_error",
    "is_retryable_model_error",
    "gemini_generate_with_retry",
    "_candidate_gemini_models",
    "_normalized_api_key_list",
    "friendly_ai_error",
}
nodes = []
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        names = []
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        elif isinstance(node.target, ast.Name):
            names = [node.target.id]
        if any(name in needed_assignments for name in names):
            nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in needed_functions:
        nodes.append(node)

namespace = {
    "base64": base64,
    "hashlib": hashlib,
    "Fernet": Fernet,
    "InvalidToken": InvalidToken,
    "types": types,
    "random": random,
    "time": time,
    "re": __import__("re"),
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

# Build both a new and legacy cipher exactly as the production code does.
legacy_secret = namespace["LEGACY_COOKIE_SECRET"]
primary_secret = "unit-test-primary-secret"
def cipher_for(secret):
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest()))
namespace["api_ciphers"] = [cipher_for(primary_secret), cipher_for(legacy_secret)]
namespace["api_cipher"] = namespace["api_ciphers"][0]

clean = namespace["_clean_api_keys"]
normalized = namespace["_normalized_api_key_list"]
encrypt = namespace["encrypt_api_keys"]
decrypt = namespace["decrypt_api_keys"]
assert clean(" key-a\nkey-a\n key-b ") == "key-a\nkey-b"
assert normalized(["key-a", "key-a", " key-b "]) == ["key-a", "key-b"]

new_token = encrypt("key-a\nkey-b")
assert decrypt(new_token) == "key-a\nkey-b"
legacy_token = cipher_for(legacy_secret).encrypt(b"old-key").decode("utf-8")
assert decrypt(legacy_token) == "old-key"

assert namespace["is_quota_error"](RuntimeError("429 RESOURCE_EXHAUSTED"))
assert namespace["is_invalid_key_error"](RuntimeError("API key reported as leaked"))
assert namespace["is_model_unavailable_error"](RuntimeError("404 NOT_FOUND"))
assert namespace["is_transient_gemini_error"](RuntimeError("503 UNAVAILABLE"))
assert namespace["is_structured_output_error"](RuntimeError("AI មិនបានត្រឡប់បន្ទាត់ SRT គ្រប់គ្រាន់"))
assert "REDACTED_API_KEY" in namespace["friendly_ai_error"](
    RuntimeError("bad request https://example.test AIza" + "a" * 35)
)

models = namespace["_candidate_gemini_models"]("gemini-3.6-flash")
assert models == ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash-lite"]

class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0
        self.last_config = None
    def generate_content(self, model, contents, config):
        self.calls += 1
        self.last_config = config
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

class FakeClient:
    def __init__(self, outcomes):
        self.models = FakeModels(outcomes)

run = namespace["gemini_generate_with_retry"]
quota_client = FakeClient([RuntimeError("429 RESOURCE_EXHAUSTED")])
try:
    run(quota_client, "gemini-3.5-flash-lite", ["prompt"])
except RuntimeError:
    pass
else:
    raise AssertionError("Quota error should be raised immediately")
assert quota_client.models.calls == 1

ok = object()
transient_client = FakeClient([RuntimeError("503 UNAVAILABLE"), ok])
assert run(transient_client, "gemini-3.5-flash-lite", ["prompt"]) is ok
assert transient_client.models.calls == 2
assert transient_client.models.last_config.response_mime_type == "application/json"

print("Gemini hardening tests: OK")
