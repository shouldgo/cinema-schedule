"""Parser for Agrafka cinema (kinoagrafka.pl)."""

import re
from dates import POLISH_MONTHS
from formatting import normalize_title


def parse(html: str) -> list[dict]:
    """
    Parse Agrafka HTML.
    Returns list of {title, date, time, day}.
    """
    results = []

    # Remove HTML comments (huge amount of old data)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    # Find all repertoire tables
    table_pattern = r'<table class="repertoire"[^>]*>(.*?)</table>'
    for table_match in re.finditer(table_pattern, html, re.DOTALL):
        table = table_match.group(1)

        # Extract date from thead h3: "24 stycznia 2026 /piątek/"
        date_match = re.search(r'<h3>([^<]+)</h3>', table)
        if not date_match:
            continue

        date_str = date_match.group(1).replace('/', ' ')
        parts = date_str.strip().split()

        if len(parts) < 4:
            continue

        day_num, month_name, year, day_name = parts[0], parts[1], parts[2], parts[3]
        month = POLISH_MONTHS.get(month_name.lower(), 1)
        iso_date = f"{year}-{month:02d}-{int(day_num):02d}"

        # Find all tbody rows
        row_pattern = r'<tr>(.*?)</tr>'
        for row_match in re.finditer(row_pattern, table, re.DOTALL):
            row = row_match.group(1)

            # Extract time
            time_match = re.search(r'<td class="hour">([^<]+)</td>', row)
            if not time_match:
                continue
            time_str = time_match.group(1).strip()

            # Extract Polish title from anchor text (not title attribute which has original title)
            # Handle optional <b> tag and whitespace: <a href="..."><b>TITLE</b> </a>
            title_match = re.search(r'<a[^>]*href="film\.php[^"]*"[^>]*>\s*(?:<b>)?([^<]+)(?:</b>)?\s*</a>', row)
            if not title_match:
                continue
            title = normalize_title(title_match.group(1))

            results.append({
                "title": title,
                "date": iso_date,
                "time": time_str,
                "day": day_name.lower(),
            })

    return results
