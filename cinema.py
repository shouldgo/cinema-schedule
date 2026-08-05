#!/usr/bin/env python3
"""Cinema schedule aggregator for Krakow cinemas."""

import sys
from datetime import date, timedelta
from pathlib import Path

from fetch import fetch_html
from formatting import format_schedule
from parsers import PARSERS

OUTPUT_FILE = Path(__file__).parent / "schedule.md"


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
    min_time: str | None = None
) -> list[dict]:
    """
    Filter screenings by date range and earliest time.

    Args:
        screenings: List of screening dicts
        from_date: Start date (inclusive)
        to_date: End date (inclusive)
        min_time: Earliest time as "HH:MM" (optional)

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


def prompt_date(label: str, default: date) -> date:
    """Prompt user for a date, with default."""
    default_str = default.isoformat()
    response = input(f"{label} [{default_str}]: ").strip()
    if not response:
        return default
    try:
        return date.fromisoformat(response)
    except ValueError:
        print(f"Invalid date format, using {default_str}")
        return default


def prompt_time(label: str) -> str | None:
    """Prompt user for minimum time (optional)."""
    response = input(f"{label}: ").strip()
    if not response:
        return None
    # Basic validation
    if len(response) == 5 and response[2] == ":":
        return response
    print("Invalid time format, ignoring filter")
    return None


def main():
    print("\nFetching...")

    all_screenings, status = fetch_all_screenings()

    for msg in status:
        print(f"  {msg}")

    if not all_screenings:
        print("\nAll cinemas failed. Check your internet connection.")
        sys.exit(1)

    print()

    # Date prompts
    today = date.today()
    from_date = prompt_date("From date", today)
    to_date = prompt_date("To date", today + timedelta(days=6))
    min_time = prompt_time("Earliest time (empty=all)")

    # Filter once, then count and format the same list
    filtered = filter_screenings(all_screenings, from_date, to_date, min_time)
    movie_count, screening_count = count_results(filtered)

    print(f"\nFound {movie_count} movies, {screening_count} screenings")

    output = format_schedule(filtered, from_date, to_date)
    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(f"Written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
