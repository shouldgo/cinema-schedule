"""Parser for Paradox cinema (kinoparadox.pl)."""

import re
from datetime import date
from dates import weekday_name
from formatting import normalize_title


def parse(html: str) -> list[dict]:
    """
    Parse Paradox HTML.
    Returns list of {title, date, time, day}.
    """
    results = []

    # Find all screening rows with data-date attribute
    pattern = r'<div class="list-item__content__row" data-date="([^"]+)"'
    matches = list(re.finditer(pattern, html))

    for i, match in enumerate(matches):
        date_str = match.group(1)  # DD.MM.YYYY
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        block = html[start:end]

        # Convert DD.MM.YYYY to YYYY-MM-DD
        parts = date_str.split('.')
        if len(parts) != 3:
            continue
        day_num, month, year = parts
        iso_date = f"{year}-{month}-{day_num}"

        # Derive day name from date
        try:
            d = date.fromisoformat(iso_date)
            day_name = weekday_name(d)
        except ValueError:
            day_name = ""

        # Extract time
        time_match = re.search(r'<div class="item-time">(\d{1,2}:\d{2})</div>', block)
        if not time_match:
            continue
        time_str = time_match.group(1)

        # Extract title
        title_match = re.search(r'class="item-title"[^>]*>\s*([^\n<]+)', block)
        if not title_match:
            continue
        title = normalize_title(title_match.group(1))

        results.append({
            "title": title,
            "date": iso_date,
            "time": time_str,
            "day": day_name,
        })

    return results
