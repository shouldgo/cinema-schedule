"""Core logic shared between CLI and GUI."""

from datetime import date

from fetch import fetch_html
from parsers import PARSERS


def fetch_all_screenings() -> tuple[list[dict], list[str]]:
    """
    Fetch and parse screenings from all cinemas.

    Returns:
        (screenings, status_messages) where screenings is list of dicts
        with keys: title, date, time, day, cinema
    """
    all_screenings = []
    status = []

    for cinema_key, (display_name, parse_fn) in PARSERS.items():
        html = fetch_html(cinema_key)

        if html is None:
            status.append(f"⚠ {display_name}: fetch failed")
            continue

        try:
            screenings = parse_fn(html)
            for s in screenings:
                s["cinema"] = display_name
            all_screenings.extend(screenings)
            status.append(f"✓ {display_name} ({len(screenings)})")

            if len(screenings) == 0:
                status.append(f"⚠ WARNING: {display_name} returned 0 screenings")
        except Exception as e:
            status.append(f"⚠ {display_name}: parse failed ({e})")

    return all_screenings, status


def filter_screenings(
    screenings: list[dict],
    from_date: date,
    to_date: date,
    min_time: str | None = None,
    max_time: str | None = None,
    cinemas: set[str] | None = None
) -> list[dict]:
    """
    Filter screenings by date range, time range, and cinemas.

    Args:
        screenings: List of screening dicts
        from_date: Start date (inclusive)
        to_date: End date (inclusive)
        min_time: Earliest time as "HH:MM" (optional)
        max_time: Latest time as "HH:MM" (optional)
        cinemas: Set of cinema names to include (None = all)

    Returns:
        Filtered list of screenings
    """
    filtered = []

    for s in screenings:
        # Date filter
        try:
            d = date.fromisoformat(s["date"])
        except ValueError:
            continue

        if d < from_date or d > to_date:
            continue

        # Time filter
        if min_time and s["time"] < min_time:
            continue
        if max_time and s["time"] > max_time:
            continue

        # Cinema filter
        if cinemas and s["cinema"] not in cinemas:
            continue

        filtered.append(s)

    return filtered


def count_results(screenings: list[dict]) -> tuple[int, int]:
    """
    Count unique movies and total screenings.

    Returns:
        (movie_count, screening_count)
    """
    titles = set(s["title"] for s in screenings)
    return len(titles), len(screenings)
