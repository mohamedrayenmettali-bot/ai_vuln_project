from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any


def _clean(value: object) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"\s+", " ", text)


def build_finding_dedupe_key(
    *,
    title: str,
    cve_id: str | None = None,
    file_path: str | None = None,
    line: int | str | None = None,
    component: str | None = None,
) -> str:
    identity = {
        "version": 1,
        "title": _clean(title),
        "cve_id": _clean(cve_id),
        "file_path": _clean(file_path),
        "line": _clean(line),
        "component": _clean(component),
    }
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_external_payload(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_external_updated_at(raw: dict[str, Any]) -> datetime | None:
    for key in ("updated", "updated_at", "last_reviewed", "date", "created"):
        value = raw.get(key)
        if not value:
            continue
        if isinstance(value, datetime):
            return _as_utc(value)
        text = str(value).strip()
        try:
            return _as_utc(datetime.fromisoformat(text.replace("Z", "+00:00")))
        except ValueError:
            continue
    return None


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
