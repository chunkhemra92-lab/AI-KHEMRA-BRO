from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from google import genai
from pydantic import BaseModel, Field

APP_VERSION = "1.0.0"
TRANSLATION_API_KEY = os.getenv("TRANSLATION_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DEFAULT_MODEL = os.getenv("TRANSLATION_MODEL", "gemini-3.8-flash").strip()
MAX_WORKERS = max(1, min(int(os.getenv("TRANSLATION_MAX_WORKERS", "3")), 6))
BATCH_SIZE = max(10, min(int(os.getenv("TRANSLATION_BATCH_SIZE", "60")), 80))

app = FastAPI(title="AI KHEMRA BRO Translation Server", version=APP_VERSION)


class Cue(BaseModel):
    id: int
    start: str = "00:00:00,000"
    end: str = "00:00:00,000"
    source: str = Field(min_length=1, max_length=4000)
    input_tag: str = "AUTO"


class TranslateRequest(BaseModel):
    cues: list[Cue] = Field(min_length=1, max_length=2000)
    target_language: str = "Khmer (ខ្មែរ)"
    style: str = "Natural movie dialogue"
    model: str | None = None


class TranslatedCue(BaseModel):
    id: int
    tag: str
    text: str


def require_api_key(x_translation_api_key: str | None = Header(default=None)) -> None:
    if not TRANSLATION_API_KEY or not x_translation_api_key or x_translation_api_key != TRANSLATION_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Translation API key is invalid")


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_json_array(raw: str) -> list[dict[str, Any]]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    left, right = cleaned.find("["), cleaned.rfind("]")
    if left < 0 or right <= left:
        raise ValueError("Model did not return a JSON array")
    value = json.loads(cleaned[left : right + 1])
    if not isinstance(value, list):
        raise ValueError("Model response is not an array")
    return value


def cue_word_limit(cue: Cue) -> int:
    # Keep the spoken translation short enough for the original subtitle slot.
    parts = cue.end.split(":")
    starts = cue.start.split(":")
    try:
        end_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2].replace(",", "."))
        start_seconds = int(starts[0]) * 3600 + int(starts[1]) * 60 + float(starts[2].replace(",", "."))
        duration = max(0.35, end_seconds - start_seconds)
    except (ValueError, IndexError):
        duration = 2.0
    return max(2, min(22, int(duration * 3 + 1)))


def prompt_for(batch: list[Cue], target_language: str, style: str) -> str:
    lines = "\n".join(
        f'ID={cue.id} | TIME={cue.start} --> {cue.end} | MAX_WORDS={cue_word_limit(cue)} | INPUT_TAG={cue.input_tag or "AUTO"} | SOURCE={cue.source}'
        for cue in batch
    )
    return f"""You are the fast, precise translation engine for AI KHEMRA BRO.
Automatically identify the source language and translate every line into {target_language}.
Use {style} for natural spoken movie dialogue.

Rules:
1. Return every input ID exactly once, in the same order. Never change IDs or timestamps.
2. Translate all meaning, including names, numbers, negations, short replies, fillers, and emotion.
3. For Khmer, use natural Cambodian spoken language and do not output Chinese, Thai, Vietnamese, or English dialogue.
4. Keep each line concise enough for MAX_WORDS without omitting meaning.
5. Tag only M, F, M_THINK, or F_THINK. Preserve INPUT_TAG when it is not AUTO.
6. Return JSON only in this exact shape: [{{"id": 1, "tag": "M", "text": "..."}}]

CUES:
{lines}"""


def call_batch(batch: list[Cue], target_language: str, style: str, model_name: str) -> list[TranslatedCue]:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured on the translation server")
    client = genai.Client(api_key=GEMINI_API_KEY)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt_for(batch, target_language, style)],
                config={"response_mime_type": "application/json"},
            )
            rows = parse_json_array(response.text or "")
            allowed = {cue.id: cue for cue in batch}
            result: dict[int, TranslatedCue] = {}
            for row in rows:
                cue_id = int(row.get("id"))
                cue = allowed.get(cue_id)
                text = normalize_text(row.get("text"))
                if cue is None or not text:
                    continue
                tag = str(row.get("tag", "M")).upper().strip()
                if tag not in {"M", "F", "M_THINK", "F_THINK"}:
                    tag = cue.input_tag if cue.input_tag in {"M", "F", "M_THINK", "F_THINK"} else "M"
                if cue.input_tag in {"M", "F", "M_THINK", "F_THINK"}:
                    tag = cue.input_tag
                result[cue_id] = TranslatedCue(id=cue_id, tag=tag, text=text)
            missing = [cue.id for cue in batch if cue.id not in result]
            if missing:
                raise RuntimeError(f"Missing translated cue IDs: {missing[:10]}")
            return [result[cue.id] for cue in batch]
        except Exception as exc:
            last_error = exc
            message = str(exc).upper()
            retryable = any(token in message for token in ("429", "503", "UNAVAILABLE", "TIMEOUT", "DEADLINE", "INTERNAL"))
            if not retryable or attempt == 2:
                raise
            time.sleep(1.2 * (2**attempt))
    raise last_error or RuntimeError("Translation failed")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-khemra-translation", "version": APP_VERSION}


@app.post("/v1/translate", response_model=list[TranslatedCue], dependencies=[Depends(require_api_key)])
def translate(request: TranslateRequest) -> list[TranslatedCue]:
    model_name = (request.model or DEFAULT_MODEL).strip()
    batches = [request.cues[offset : offset + BATCH_SIZE] for offset in range(0, len(request.cues), BATCH_SIZE)]
    results: dict[int, TranslatedCue] = {}
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(batches))) as executor:
        futures = {
            executor.submit(call_batch, batch, request.target_language, request.style, model_name): index
            for index, batch in enumerate(batches)
        }
        try:
            for future in as_completed(futures):
                for cue in future.result():
                    results[cue.id] = cue
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Translation provider failed: {str(exc)[:300]}") from exc
    missing = [cue.id for cue in request.cues if cue.id not in results]
    if missing:
        raise HTTPException(status_code=502, detail=f"Missing translated IDs: {missing[:20]}")
    return [results[cue.id] for cue in request.cues]
