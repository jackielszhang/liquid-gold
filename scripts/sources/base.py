from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AdapterResult:
    ok: bool
    payload: dict | None
    error: str | None = None
    source_url: str | None = None
    path: Path | None = None
