"""Parser for KIKA cinema (bilety.kinokika.pl)."""

import re
from dates import weekday_name
from datetime import date
from formatting import normalize_title


def parse(html: str) -> list[dict]:
    """
    Parse KIKA HTML.
    Returns list of {title, date, time, day}.
    """
    results = []

    # Split by repertoire-once row blocks with date in class
    pattern = r'<div class="repertoire-once row (\d{4}-\d{2}-\d{2})[^"]*"'
    matches = list(re.finditer(pattern, html))

    for i, match in enumerate(matches):
        iso_date = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        block = html[start:end]

        # Extract title from: <a title="Kup bilet - TITLE"
        title_match = re.search(r'<a title="Kup bilet - ([^"]+)"', block)
        if not title_match:
            continue
        title = normalize_title(title_match.group(1))

        # Extract day name from date line
        day_name = ""
        day_match = re.search(r'fa-calendar[^>]*>[^<]*</i>\s*([^,]+),', block)
        if day_match:
            day_name = day_match.group(1).strip().lower()

        # Fallback: derive from date
        if not day_name:
            try:
                d = date.fromisoformat(iso_date)
                day_name = weekday_name(d)
            except ValueError:
                pass

        # Extract time from: godz. HH:MM
        time_match = re.search(r'godz\.\s*(\d{1,2}:\d{2})', block)
        if not time_match:
            continue
        time_str = time_match.group(1)

        results.append({
            "title": title,
            "date": iso_date,
            "time": time_str,
            "day": day_name,
        })

    return results
