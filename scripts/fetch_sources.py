"""Download helpers with retries, discovery, and content-type awareness.

SA fuel sources rotate file URLs daily/monthly. We discover the latest PDF
from a stable listing page, then download with a browser-like User-Agent.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 (compatible; LiquidGold/1.0; +https://github.com/jackielszhang/liquid-gold)"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Stable listing pages — not the daily/monthly file URLs themselves.
CEF_DAILY_INDEX_URL = "https://cefgroup.co.za/daily-basic-fuel-price/"
CEF_MONTHLY_INDEX_URL = "https://cefgroup.co.za/monthly-press-release/"

DAILY_PDF_RE = re.compile(
    r"(https?://[^\s\"'<>]+/Daily-(\d{2})-(\d{2})-(\d{4})\.pdf)",
    re.IGNORECASE,
)
DAILY_PDF_REL_RE = re.compile(
    r"(/wp-content/uploads/[^\s\"'<>]*Daily-(\d{2})-(\d{2})-(\d{4})\.pdf)",
    re.IGNORECASE,
)
PRESS_PDF_RE = re.compile(
    r"(https?://[^\s\"'<>]+/Press-[Rr]elease-[^\s\"'<>]+\.pdf)",
    re.IGNORECASE,
)
PRESS_PDF_REL_RE = re.compile(
    r"(/wp-content/uploads/[^\s\"'<>]*Press-[Rr]elease-[^\s\"'<>]+\.pdf)",
    re.IGNORECASE,
)
YEAR_PAGE_RE = re.compile(r"https?://cefgroup\.co\.za/(\d{4})-(\d+)/?", re.IGNORECASE)
CHANGE_DATE_RE = re.compile(
    r"Change-(\d{2})-([A-Za-z]+)-(\d{2,4})",
    re.IGNORECASE,
)

MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "febuary": 2,  # CEF typo seen in the wild
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


@dataclass
class DownloadResult:
    url: str
    path: Path
    content_type: str | None


def _request(url: str, timeout: int = DEFAULT_TIMEOUT):
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
        },
    )
    return urlopen(request, timeout=timeout)


def fetch_bytes(url: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[bytes, str | None, str]:
    """GET url with retries. Returns (body, content_type, final_url)."""

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with _request(url, timeout=timeout) as response:
                body = response.read()
                content_type = response.headers.get_content_type()
                final_url = response.geturl()
                return body, content_type, final_url
        except (OSError, URLError, TimeoutError, HTTPError) as exc:
            last_error = exc
            # Brief backoff: 1s, 2s, 4s before giving up.
            if attempt < MAX_RETRIES - 1:
                time.sleep(2**attempt)
    raise URLError(f"failed to fetch {url}: {last_error}")


def fetch_text(url: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[str, str]:
    body, _, final_url = fetch_bytes(url, timeout=timeout)
    return body.decode("utf-8", errors="replace"), final_url


def _extension_for(content_type: str | None, url: str, body: bytes) -> str:
    """Prefer magic bytes / Content-Type over the URL path suffix."""

    if body.startswith(b"%PDF"):
        return ".pdf"
    lowered = (content_type or "").lower()
    if "pdf" in lowered:
        return ".pdf"
    if "html" in lowered:
        return ".html"
    if "csv" in lowered or "text/plain" in lowered:
        path_name = Path(urlparse(url).path).name
        if "." in path_name:
            return Path(path_name).suffix.lower()
        return ".txt" if "text/plain" in lowered else ".csv"
    path_name = Path(urlparse(url).path).name
    suffix = Path(path_name).suffix.lower()
    return suffix if suffix else ".bin"


def download(url: str, destination_dir: Path) -> DownloadResult:
    destination_dir.mkdir(parents=True, exist_ok=True)
    body, content_type, final_url = fetch_bytes(url)
    parsed = urlparse(final_url)
    stem = Path(parsed.path).stem or "downloaded-source"
    extension = _extension_for(content_type, final_url, body)
    destination = destination_dir / f"{stem}{extension}"
    destination.write_bytes(body)
    return DownloadResult(url=final_url, path=destination, content_type=content_type)


def safe_download(url: str | None, destination_dir: Path) -> DownloadResult | None:
    if not url:
        return None
    try:
        return download(url, destination_dir)
    except (OSError, URLError, TimeoutError, HTTPError, ValueError):
        return None


def _pick_year_page(index_html: str, base_url: str) -> str:
    """Choose the newest CEF year archive linked from an index page."""

    candidates: list[tuple[int, int, str]] = []
    for match in YEAR_PAGE_RE.finditer(index_html):
        year = int(match.group(1))
        slug = int(match.group(2))
        candidates.append((year, slug, match.group(0)))
    if not candidates:
        raise ValueError(f"no CEF year pages found at {base_url}")
    candidates.sort(reverse=True)
    return candidates[0][2]


def discover_latest_cef_daily_pdf(index_url: str = CEF_DAILY_INDEX_URL) -> str:
    """Resolve the newest Daily-DD-MM-YYYY.pdf from the CEF daily index."""

    index_html, index_final = fetch_text(index_url)
    year_page = _pick_year_page(index_html, index_final)
    year_html, year_final = fetch_text(year_page)

    found: list[tuple[date, str]] = []
    for match in DAILY_PDF_RE.finditer(year_html):
        day, month, year = int(match.group(2)), int(match.group(3)), int(match.group(4))
        found.append((date(year, month, day), match.group(1)))
    for match in DAILY_PDF_REL_RE.finditer(year_html):
        day, month, year = int(match.group(2)), int(match.group(3)), int(match.group(4))
        found.append((date(year, month, day), urljoin(year_final, match.group(1))))

    if not found:
        raise ValueError(f"no Daily-*.pdf links found on {year_page}")
    found.sort(key=lambda item: item[0], reverse=True)
    return found[0][1]


def _press_release_sort_key(url: str) -> date:
    """Prefer the 'Change-DD-Month-YYYY' effective date embedded in CEF filenames."""

    match = CHANGE_DATE_RE.search(url)
    if match:
        day = int(match.group(1))
        month = MONTH_NAMES.get(match.group(2).lower())
        year_raw = match.group(3)
        year = int(year_raw) if len(year_raw) == 4 else 2000 + int(year_raw)
        if month:
            return date(year, month, day)

    # Fall back to the upload folder year/month when the filename is odd.
    folder = re.search(r"/uploads/(\d{4})/(\d{2})/", url)
    if folder:
        return date(int(folder.group(1)), int(folder.group(2)), 1)
    return date.min


def discover_latest_cef_press_release(index_url: str = CEF_MONTHLY_INDEX_URL) -> str:
    """Resolve the newest monthly press-release PDF (official adjustment)."""

    index_html, index_final = fetch_text(index_url)
    year_page = _pick_year_page(index_html, index_final)
    year_html, year_final = fetch_text(year_page)

    urls: list[str] = []
    for match in PRESS_PDF_RE.finditer(year_html):
        urls.append(match.group(1))
    for match in PRESS_PDF_REL_RE.finditer(year_html):
        urls.append(urljoin(year_final, match.group(1)))

    # De-dupe while keeping order.
    unique: list[str] = list(dict.fromkeys(urls))
    if not unique:
        raise ValueError(f"no Press-Release PDFs found on {year_page}")
    unique.sort(key=_press_release_sort_key, reverse=True)
    return unique[0]
