"""Parser for Kijów cinema (kupbilet.kijow.pl)."""

import re
import html as html_module
from datetime import date
from dates import weekday_name
from formatting import normalize_title


def parse(html: str) -> list[dict]:
    """
    Parse Kijów HTML (extracts from embedded JavaScript).
    Returns list of {title, date, time, day}.
    """
    results = []

    # Extract from JavaScript data structure
    js_pattern = r"'Id': (\d+), 'Name': '([^']+)', 'Date': '([^']+)', 'Hour': '([^']+)'"

    for match in re.finditer(js_pattern, html):
        _, name, date_str, hour = match.groups()

        # Decode HTML entities and normalize
        title = normalize_title(html_module.unescape(name))

        # Convert DD.MM.YYYY to YYYY-MM-DD
        parts = date_str.split('.')
        if len(parts) != 3:
            continue

        day_num, month, year = parts
        iso_date = f"{year}-{month.zfill(2)}-{day_num.zfill(2)}"

        # Derive day name from date
        try:
            d = date.fromisoformat(iso_date)
            day_name = weekday_name(d)
        except ValueError:
            day_name = ""

        results.append({
            "title": title,
            "date": iso_date,
            "time": hour,
            "day": day_name,
        })

    return results
