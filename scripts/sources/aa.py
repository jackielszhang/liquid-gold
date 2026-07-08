from __future__ import annotations

from pathlib import Path

from scripts.sources.base import AdapterResult


def parse(path: Path, source_url: str) -> AdapterResult:
    text = path.read_text(encoding="utf-8")
    return AdapterResult(ok=True, payload={"snippet": text[:300]}, source_url=source_url, path=path)
