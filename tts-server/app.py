from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path

import edge_tts
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel, Field

APP_VERSION = "1.0.0"
TTS_API_KEY = os.getenv("TTS_API_KEY", "").strip()
MAX_WORKERS = max(1, min(int(os.getenv("TTS_MAX_WORKERS", "4")), 6))
REQUEST_TIMEOUT = max(20, int(os.getenv("TTS_REQUEST_TIMEOUT_SECONDS", "75")))

PISITH = "km-KH-PisethNeural"
SREYMOM = "km-KH-SreymomNeural"
VOICE_PROFILES = {
    "M": {"voice": PISITH, "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"},
    "F": {"voice": SREYMOM, "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"},
    "M_THINK": {"voice": PISITH, "rate": "-2%", "pitch": "-1Hz", "volume": "-1%"},
    "F_THINK": {"voice": SREYMOM, "rate": "-2%", "pitch": "-1Hz", "volume": "-1%"},
}

app = FastAPI(title="AI KHEMRA BRO TTS Server", version=APP_VERSION)


class TTSCue(BaseModel):
    id: int
    text: str = Field(min_length=1, max_length=4000)
    tag: str = "M"


class TTSRequest(BaseModel):
    cues: list[TTSCue] = Field(min_length=1, max_length=600)
    output_name: str = Field(default="khemra-tts", max_length=80)


def require_api_key(x_tts_api_key: str | None = Header(default=None, alias="X-TTS-API-Key")) -> None:
    if not TTS_API_KEY or not x_tts_api_key or x_tts_api_key != TTS_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="TTS API key is invalid")


def lock_tag(tag: str) -> str:
    normalized = re.sub(r"[\s_-]+", "", str(tag or "").upper())
    if normalized in {"MTHINK", "MALETHINK", "INNERMALE"}:
        return "M_THINK"
    if normalized in {"FTHINK", "FEMALETHINK", "INNERFEMALE"}:
        return "F_THINK"
    return "F" if normalized in {"F", "FEMALE", "GIRL"} else "M"


def prepare_text(text: str) -> str:
    # Role tags are metadata, not words to be spoken by Edge TTS.
    cleaned = re.sub(r"\[(?:M|F|M_THINK|F_THINK|MALE|FEMALE)\]\s*", "", str(text or ""), flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        raise ValueError("TTS cue is empty")
    return cleaned


def polish_clip(source: Path, target: Path, tag: str) -> None:
    # Conservative filtering: retain Khmer clarity, remove harsh highs, and
    # normalize loudness without stereo widening or artificial echo.
    filters = [
        "highpass=f=85:p=2",
        "lowpass=f=6800:p=2",
        "equalizer=f=3400:t=q:w=1.0:g=-1.5",
        "acompressor=threshold=-24dB:ratio=1.65:attack=16:release=220:makeup=1.0:knee=5",
        "loudnorm=I=-16:TP=-1.5:LRA=7",
        "volume=-1dB" if tag in {"M_THINK", "F_THINK"} else "volume=0dB",
        "alimiter=limit=0.90:attack=8:release=120",
    ]
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-i", str(source),
            "-af", ",".join(filters), "-c:a", "libmp3lame", "-ac", "2", "-ar", "48000",
            "-b:a", "128k", str(target),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0 or not target.exists() or target.stat().st_size < 1000:
        raise RuntimeError((result.stderr or "FFmpeg audio polish failed")[-800:])


async def render_one(cue: TTSCue, folder: Path) -> dict:
    tag = lock_tag(cue.tag)
    profile = VOICE_PROFILES[tag]
    clean_text = prepare_text(cue.text)
    raw = folder / f"{cue.id:05d}.raw.mp3"
    final = folder / f"{cue.id:05d}_{tag}.mp3"
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            raw.unlink(missing_ok=True)
            await asyncio.wait_for(
                edge_tts.Communicate(
                    text=clean_text,
                    voice=profile["voice"],
                    rate=profile["rate"],
                    pitch=profile["pitch"],
                    volume=profile["volume"],
                ).save(str(raw)),
                timeout=REQUEST_TIMEOUT,
            )
            if raw.exists() and raw.stat().st_size > 500:
                await asyncio.to_thread(polish_clip, raw, final, tag)
                raw.unlink(missing_ok=True)
                return {"id": cue.id, "tag": tag, "file": final.name, "text": clean_text}
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.8 * (attempt + 1))
    raise RuntimeError(f"TTS failed for cue {cue.id}: {last_error}")


def cleanup(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-khemra-tts", "version": APP_VERSION}


@app.post("/v1/synthesize", dependencies=[Depends(require_api_key)])
async def synthesize(request: TTSRequest) -> FileResponse:
    folder = Path(tempfile.mkdtemp(prefix="khemra-tts-"))
    try:
        semaphore = asyncio.Semaphore(MAX_WORKERS)

        async def limited(cue: TTSCue) -> dict:
            async with semaphore:
                return await render_one(cue, folder)

        results = await asyncio.gather(*(limited(cue) for cue in request.cues))
        results.sort(key=lambda row: row["id"])
        manifest = folder / "manifest.json"
        manifest.write_text(json.dumps({"version": APP_VERSION, "cues": results}, ensure_ascii=False, indent=2), encoding="utf-8")
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", request.output_name).strip("-") or "khemra-tts"
        archive = folder / f"{safe_name}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.write(manifest, "manifest.json")
            for row in results:
                bundle.write(folder / row["file"], row["file"])
        return FileResponse(
            archive,
            media_type="application/zip",
            filename=f"{safe_name}.zip",
            background=BackgroundTask(cleanup, folder),
        )
    except Exception as exc:
        cleanup(folder)
        raise HTTPException(status_code=502, detail=str(exc)[:500]) from exc
