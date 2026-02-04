"""HTTP fetching with file caching."""

import os
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_MAX_AGE = 3600  # 1 hour

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# Cinema URLs and their encodings
CINEMAS = {
    "kika": ("https://bilety.kinokika.pl", "utf-8"),
    "mikro": ("https://kinomikro.pl/repertoire/?view=all", "utf-8"),
    "agrafka": ("https://kinoagrafka.pl/rep.php", "utf-8"),
    "paradox": ("https://kinoparadox.pl/repertuar/", "utf-8"),
    "baranami": ("https://www.kinopodbaranami.pl/repertuar.php", "iso-8859-2"),
    "kijow": ("https://kupbilet.kijow.pl/MSI/mvc/pl", "utf-8"),
}


def ensure_cache_dir():
    CACHE_DIR.mkdir(exist_ok=True)


def cache_path(cinema: str) -> Path:
    return CACHE_DIR / f"{cinema}.html"


def is_cache_valid(cinema: str) -> bool:
    """Check if cache exists and is less than CACHE_MAX_AGE seconds old."""
    path = cache_path(cinema)
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < CACHE_MAX_AGE


def fetch_html(cinema: str, force: bool = False) -> str | None:
    """
    Fetch HTML for a cinema, using cache if valid.
    Returns HTML string or None on error.
    """
    ensure_cache_dir()
    path = cache_path(cinema)
    url, encoding = CINEMAS[cinema]

    # Use cache if valid and not forced
    if not force and is_cache_valid(cinema):
        return path.read_text(encoding='utf-8', errors='replace')

    # Fetch from web
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=30) as response:
            raw = response.read()
            html = raw.decode(encoding, errors='replace')
            # Save to cache
            path.write_text(html, encoding='utf-8')
            return html
    except (URLError, HTTPError, TimeoutError) as e:
        return None


def fetch_all(force: bool = False) -> dict[str, str | None]:
    """
    Fetch HTML for all cinemas.
    Returns dict of cinema -> HTML or None.
    """
    results = {}
    for cinema in CINEMAS:
        results[cinema] = fetch_html(cinema, force=force)
    return results
