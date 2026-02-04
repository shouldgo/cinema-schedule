#!/usr/bin/env python3
"""Cinema schedule aggregator for Krakow cinemas."""

import sys
from datetime import date, timedelta
from pathlib import Path

from core import fetch_all_screenings, filter_screenings, count_results
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

    # Filter and count
    filtered = filter_screenings(all_screenings, from_date, to_date, min_time)
    movie_count, screening_count = count_results(filtered)

    print(f"\nFound {movie_count} movies, {screening_count} screenings")

    # Format and write output
    output = format_schedule(all_screenings, from_date, to_date, min_time)
    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(f"Written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
