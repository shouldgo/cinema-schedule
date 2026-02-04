"""Parser for Pod Baranami cinema (kinopodbaranami.pl)."""

import re
from dates import POLISH_MONTHS
from formatting import normalize_title

DAYS_PL = {
    'Poniedziałek': 'poniedziałek', 'Wtorek': 'wtorek', 'Środa': 'środa',
    'Czwartek': 'czwartek', 'Piątek': 'piątek', 'Sobota': 'sobota', 'Niedziela': 'niedziela'
}


def parse(html: str) -> list[dict]:
    """
    Parse Pod Baranami HTML.
    Returns list of {title, date, time, day}.
    """
    results = []

    # Split by date headers: <p class="rep_date"><span>Dzień</span> DD miesiąc //
    sections = re.split(r'<p class="rep_date"><span>([^<]+)</span>\s+(\d+)\s+(\w+)\s+//', html)

    # sections layout: [before, day1, num1, month1, content1, day2, num2, month2, content2, ...]
    for i in range(1, len(sections), 4):
        if i + 3 >= len(sections):
            break

        day_name_raw = sections[i].strip()
        day_num = sections[i + 1].strip()
        month_name = sections[i + 2].strip()
        content = sections[i + 3]

        day_name = DAYS_PL.get(day_name_raw, day_name_raw.lower())
        month = POLISH_MONTHS.get(month_name.lower(), 1)

        # Infer year from onclick handlers
        year_match = re.search(r"validateAndShowOrderDialog\([^,]+,[^,]+,'(\d{4})'", content)
        year = year_match.group(1) if year_match else "2026"

        iso_date = f"{year}-{month:02d}-{int(day_num):02d}"

        # Find all list items with title and time
        # Extract Polish title from anchor text (first text node before any nested tags)
        li_pattern = r'<li[^>]*>.*?<a[^>]*href="film\.php[^"]*"[^>]*>\s*([^<]+?)\s*(?:<|</a>).*?<span>.*?(\d{1,2}:\d{2}).*?</span>.*?</li>'
        for li_match in re.finditer(li_pattern, content, re.DOTALL):
            title = normalize_title(li_match.group(1).strip())
            time_str = li_match.group(2).strip()

            if title and time_str:
                results.append({
                    "title": title,
                    "date": iso_date,
                    "time": time_str,
                    "day": day_name,
                })

    return results
