from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

APP_VERSION = "1.0.0"
DB_PATH = Path(os.getenv("LICENSE_DB_PATH", "/var/lib/ai-khemra-license/licenses.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LICENSE_PEPPER = os.getenv("LICENSE_PEPPER", "").strip()
ADMIN_KEY = os.getenv("LICENSE_ADMIN_KEY", "").strip()
SERVICE_KEY = os.getenv("LICENSE_SERVICE_KEY", "").strip()
ALLOWED_DURATIONS = {7, 30, 90, 180, 365}

app = FastAPI(title="AI KHEMRA BRO License Server", version=APP_VERSION)


class CreateLicenseRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=80)
    duration_days: int = Field(default=365)
    access_code: str | None = Field(default=None, max_length=48)


class RenewLicenseRequest(BaseModel):
    duration_days: int = Field(default=365)


class ValidateLicenseRequest(BaseModel):
    access_code: str = Field(min_length=4, max_length=48)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def normalize_code(value: str) -> str:
    return re.sub(r"[^A-Z0-9_-]", "", str(value or "").strip().upper())[:48]


def normalize_name(value: str) -> str:
    return " ".join(str(value or "").strip().split())[:80]


def code_hash(code: str) -> str:
    if not LICENSE_PEPPER:
        raise RuntimeError("LICENSE_PEPPER is not configured")
    return hmac.new(LICENSE_PEPPER.encode(), code.encode(), hashlib.sha256).hexdigest()


def connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db() -> None:
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                access_code_hash TEXT NOT NULL UNIQUE,
                access_code_display TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                last_validated_at TEXT,
                plan_label TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_license_expiry ON licenses(expires_at)")
        conn.commit()


def require_admin(x_license_admin_key: str | None = Header(default=None)) -> None:
    if not ADMIN_KEY or not x_license_admin_key or not hmac.compare_digest(x_license_admin_key, ADMIN_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin license key is invalid")


def require_service(x_license_service_key: str | None = Header(default=None)) -> None:
    if not SERVICE_KEY or not x_license_service_key or not hmac.compare_digest(x_license_service_key, SERVICE_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Service license key is invalid")


def duration_label(days: int) -> str:
    return {7: "7 days", 30: "1 month", 90: "3 months", 180: "6 months", 365: "1 year"}[days]


def generated_code() -> str:
    return "KHBR-" + secrets.token_hex(6).upper()


def public_row(row: sqlite3.Row, include_code: bool = False) -> dict[str, Any]:
    result = {
        "id": row["id"],
        "customer_name": row["customer_name"],
        "created_at": row["created_at"],
        "expires_at": row["expires_at"],
        "is_active": bool(row["is_active"]),
        "plan": row["plan_label"],
    }
    if include_code:
        result["access_code"] = row["access_code_display"]
    return result


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-khemra-license", "version": APP_VERSION}


@app.post("/v1/licenses", dependencies=[Depends(require_admin)])
def create_license(request: CreateLicenseRequest) -> dict[str, Any]:
    name = normalize_name(request.customer_name)
    if not name:
        raise HTTPException(400, "customer_name is required")
    if request.duration_days not in ALLOWED_DURATIONS:
        raise HTTPException(400, "duration_days must be 7, 30, 90, 180, or 365")
    code = normalize_code(request.access_code or generated_code())
    if len(code) < 4:
        raise HTTPException(400, "access_code is too short")
    now = utcnow()
    expires = now + timedelta(days=request.duration_days)
    try:
        with connection() as conn:
            cursor = conn.execute(
                """INSERT INTO licenses
                (customer_name, access_code_hash, access_code_display, created_at, expires_at, is_active, plan_label)
                VALUES (?, ?, ?, ?, ?, 1, ?)""",
                (name, code_hash(code), code, iso(now), iso(expires), duration_label(request.duration_days),),
            )
            row = conn.execute("SELECT * FROM licenses WHERE id=?", (cursor.lastrowid,)).fetchone()
            conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Access Code already exists")
    return public_row(row, include_code=True)


@app.post("/v1/licenses/validate", dependencies=[Depends(require_service)])
def validate_license(request: ValidateLicenseRequest) -> dict[str, Any]:
    code = normalize_code(request.access_code)
    now = utcnow()
    with connection() as conn:
        row = conn.execute("SELECT * FROM licenses WHERE access_code_hash=? OR access_code_display=?", (code_hash(code), code)).fetchone()
        if row is None:
            return {"valid": False, "reason": "not_found"}
        if not bool(row["is_active"]):
            return {"valid": False, "reason": "revoked"}
        if now >= parse_iso(row["expires_at"]):
            conn.execute("UPDATE licenses SET is_active=0 WHERE id=?", (row["id"],))
            conn.commit()
            return {"valid": False, "reason": "expired", "expires_at": row["expires_at"]}
        conn.execute("UPDATE licenses SET last_validated_at=? WHERE id=?", (iso(now), row["id"]))
        conn.commit()
    return {"valid": True, "customer_name": row["customer_name"], "expires_at": row["expires_at"], "plan": row["plan_label"]}


@app.post("/v1/licenses/{license_id}/renew", dependencies=[Depends(require_admin)])
def renew_license(license_id: int, request: RenewLicenseRequest) -> dict[str, Any]:
    if request.duration_days not in ALLOWED_DURATIONS:
        raise HTTPException(400, "duration_days must be 7, 30, 90, 180, or 365")
    now = utcnow()
    with connection() as conn:
        row = conn.execute("SELECT * FROM licenses WHERE id=?", (license_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "License not found")
        base = max(parse_iso(row["expires_at"]), now)
        expires = base + timedelta(days=request.duration_days)
        conn.execute("UPDATE licenses SET expires_at=?, is_active=1, plan_label=? WHERE id=?", (iso(expires), duration_label(request.duration_days), license_id))
        row = conn.execute("SELECT * FROM licenses WHERE id=?", (license_id,)).fetchone()
        conn.commit()
    return public_row(row, include_code=True)


@app.post("/v1/licenses/{license_id}/revoke", dependencies=[Depends(require_admin)])
def revoke_license(license_id: int) -> dict[str, Any]:
    with connection() as conn:
        row = conn.execute("SELECT * FROM licenses WHERE id=?", (license_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "License not found")
        conn.execute("UPDATE licenses SET is_active=0 WHERE id=?", (license_id,))
        conn.commit()
    return {"revoked": True, "id": license_id}


@app.get("/v1/licenses", dependencies=[Depends(require_admin)])
def list_licenses() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM licenses ORDER BY id DESC").fetchall()
    return [public_row(row) for row in rows]
