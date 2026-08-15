"""Automobile Association adapter.

v1 only stores a snippet. The pipeline still downloads it so a later
cross-check can land without changing update_fuel_data.py's source list.
"""

from __future__ import annotations

from pathlib import Path

from scripts.sources.base import AdapterResult


def parse(path: Path, source_url: str) -> AdapterResult:
    text = path.read_text(encoding="utf-8")
    return AdapterResult(ok=True, payload={"snippet": text[:300]}, source_url=source_url, path=path)
