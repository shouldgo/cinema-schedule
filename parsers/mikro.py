"""Parser for Mikro cinema (kinomikro.pl)."""

import re
from datetime import date
from dates import weekday_name, WEEKDAYS
from formatting import normalize_title


def parse(html: str) -> list[dict]:
    """
    Parse Mikro HTML.
    Returns list of {title, date, time, day}.
    """
    results = []
    today = date.today()
    current_year = today.year

    # Split by date separators
    sections = re.split(r'<div class="repertoire-separator">([^<]+)</div>', html)

    # sections[0] is content before first separator
    # sections[1] is first date, sections[2] is content after first date, etc.
    for i in range(1, len(sections), 2):
        if i + 1 >= len(sections):
            break

        date_str = sections[i].strip()
        content = sections[i + 1]

        # Handle "Dzisiaj" (Today)
        if date_str == "Dzisiaj":
            iso_date = today.isoformat()
            day_name = weekday_name(today)
        else:
            # Parse "sobota - 24/1" or "piątek - 7/2"
            parts = date_str.split(' - ')
            if len(parts) != 2:
                continue

            day_name = parts[0].strip().lower()
            date_part = parts[1].strip()

            # Parse DD/M or D/M
            dm = date_part.split('/')
            if len(dm) != 2:
                continue

            day_num, month = int(dm[0]), int(dm[1])

            # Infer year - if month < today's month and we're late in year, it's next year
            year = current_year
            if month < today.month and today.month >= 10:
                year = current_year + 1

            iso_date = f"{year}-{month:02d}-{day_num:02d}"

        # Find all repertoire items
        item_pattern = r'<div class="repertoire-item[^"]*"[^>]*>(.*?)</div>\s*</div>'
        for item_match in re.finditer(item_pattern, content, re.DOTALL):
            item = item_match.group(1)

            # Extract time
            time_match = re.search(r'<p class="repertoire-item-hour">([^<]+)</p>', item)
            if not time_match:
                continue
            time_str = time_match.group(1).strip()

            # Extract title
            title_match = re.search(r'repertoire-item-title"[^>]*>([^<]+)</a>', item)
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
