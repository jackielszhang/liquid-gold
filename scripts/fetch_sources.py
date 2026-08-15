"""Download source files without letting a dead URL kill the pipeline.

GitHub Actions should still produce a dataset on a fresh clone, so a missing
or unreachable URL is treated as "use the fixture" rather than an exception.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


@dataclass
class DownloadResult:
    url: str
    path: Path
    content_type: str | None


def download(url: str, destination_dir: Path) -> DownloadResult:
    destination_dir.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(url)
    name = Path(parsed.path).name or "downloaded-source"
    destination = destination_dir / name
    with urlopen(url, timeout=30) as response:
        destination.write_bytes(response.read())
        return DownloadResult(
            url=url,
            path=destination,
            content_type=response.headers.get_content_type(),
        )


def safe_download(url: str | None, destination_dir: Path) -> DownloadResult | None:
    if not url:
        return None
    try:
        return download(url, destination_dir)
    except (OSError, URLError, TimeoutError):
        return None
