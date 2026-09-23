"""Parser for Mikro cinema (kinomikro.pl).

The site renders its repertoire client-side from a JSON API on
bilety.kinomikro.pl, so this parses JSON rather than HTML. One feed covers
both venues; they are told apart by `location.id`.
"""

import json
from datetime import date
from dates import weekday_name
from formatting import normalize_title

# Sala Mikro + Sala Mikroffala at ul. Lea 5 — the site's own JS groups these.
MIKRO_LOCATIONS = {3, 13}
# Galeria Bronowice, ul. Stawowa 61.
BRONOWICE_LOCATIONS = {8}


def _parse(text: str, location_ids: set[int]) -> list[dict]:
    """
    Parse the repertoire JSON, keeping screenings at the given locations.
    Returns list of {title, date, time, day}.
    """
    results = []
    for item in json.loads(text)["repertoires"].values():
        if item["location"]["id"] not in location_ids:
            continue

        # "2026-09-23T12:00:00+02:00" — already Warsaw local time, zero-padded.
        stamp = item["date"]
        iso_date = stamp[:10]

        results.append({
            "title": normalize_title(item["title"]),
            "date": iso_date,
            "time": stamp[11:16],
            "day": weekday_name(date.fromisoformat(iso_date)),
        })

    return results


def parse(text: str) -> list[dict]:
    """Mikro (Lea 5) screenings."""
    return _parse(text, MIKRO_LOCATIONS)


def parse_bronowice(text: str) -> list[dict]:
    """Mikro Bronowice screenings."""
    return _parse(text, BRONOWICE_LOCATIONS)
