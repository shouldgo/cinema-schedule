#!/usr/bin/env python3
"""Cinema schedule aggregator for Krakow cinemas."""

import sys
from datetime import date, timedelta
from pathlib import Path

from fetch import fetch_html, CINEMAS
from parsers import PARSERS
from formatting import format_schedule

OUTPUT_FILE = Path(__file__).parent / "schedule.md"


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

    all_screenings = []
    success_count = 0
    fail_count = 0
    screening_counts = {}  # Track per-cinema counts for validation

    for cinema_key, (display_name, parse_fn) in PARSERS.items():
        html = fetch_html(cinema_key)

        if html is None:
            print(f"  ⚠ {display_name}: fetch failed, skipping")
            fail_count += 1
            continue

        try:
            screenings = parse_fn(html)
            # Add cinema name to each screening
            for s in screenings:
                s["cinema"] = display_name
            all_screenings.extend(screenings)
            screening_counts[display_name] = len(screenings)
            print(f"  ✓ {display_name} ({len(screenings)} screenings)")
            success_count += 1
        except Exception as e:
            print(f"  ⚠ {display_name}: parse failed ({e}), skipping")
            fail_count += 1

    # Warn about cinemas that returned 0 screenings (possible parser breakage)
    for name, count in screening_counts.items():
        if count == 0:
            print(f"  ⚠ WARNING: {name} returned 0 screenings - check parser")

    if success_count == 0:
        print("\nAll cinemas failed. Check your internet connection.")
        sys.exit(1)

    print()

    # Date prompts
    today = date.today()
    from_date = prompt_date("From date", today)
    to_date = prompt_date("To date", today + timedelta(days=6))
    min_time = prompt_time("Earliest time (empty=all)")

    # Count unique movies
    movie_titles = set()
    screening_count = 0
    for s in all_screenings:
        try:
            d = date.fromisoformat(s["date"])
            if from_date <= d <= to_date:
                if min_time is None or s["time"] >= min_time:
                    movie_titles.add(s["title"])
                    screening_count += 1
        except ValueError:
            pass

    print(f"\nFound {len(movie_titles)} movies, {screening_count} screenings")

    # Format and write output
    output = format_schedule(all_screenings, from_date, to_date, min_time)
    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(f"Written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
