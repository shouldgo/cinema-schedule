"""Polish date utilities and day collapsing."""

from datetime import date

POLISH_MONTHS = {
    'stycznia': 1, 'lutego': 2, 'marca': 3, 'kwietnia': 4,
    'maja': 5, 'czerwca': 6, 'lipca': 7, 'sierpnia': 8,
    'września': 9, 'października': 10, 'listopada': 11, 'grudnia': 12
}

POLISH_MONTHS_SHORT = {
    'sty': 1, 'lut': 2, 'mar': 3, 'kwi': 4,
    'maj': 5, 'cze': 6, 'lip': 7, 'sie': 8,
    'wrz': 9, 'paź': 10, 'lis': 11, 'gru': 12
}

WEEKDAYS = ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela']
WEEKDAYS_SHORT = ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'So', 'Nd']


def weekday_name(d: date) -> str:
    """Return Polish weekday name for a date."""
    return WEEKDAYS[d.weekday()]


def weekday_short(d: date) -> str:
    """Return short Polish weekday name for a date."""
    return WEEKDAYS_SHORT[d.weekday()]


def collapse_days(dates: list[date]) -> str:
    """
    Collapse consecutive dates into ranges.

    Examples:
        [Mon, Tue, Wed] -> "Pn-śr"
        [Mon, Wed, Fri] -> "Pn, śr, pt"
        [Mon, Tue, Thu, Fri] -> "Pn-wt, cz-pt"
    """
    if not dates:
        return ""

    dates = sorted(set(dates))
    if len(dates) == 1:
        return WEEKDAYS_SHORT[dates[0].weekday()]

    # Group into consecutive runs
    runs = []
    current_run = [dates[0]]

    for d in dates[1:]:
        prev = current_run[-1]
        # Check if consecutive (1 day apart)
        if (d - prev).days == 1:
            current_run.append(d)
        else:
            runs.append(current_run)
            current_run = [d]
    runs.append(current_run)

    # Format each run
    parts = []
    for run in runs:
        if len(run) >= 3:
            # Range: "Pn-śr"
            start = WEEKDAYS_SHORT[run[0].weekday()].lower()
            end = WEEKDAYS_SHORT[run[-1].weekday()].lower()
            parts.append(f"{start.capitalize()}-{end}")
        elif len(run) == 2:
            # Two days: "Pn-wt"
            start = WEEKDAYS_SHORT[run[0].weekday()].lower()
            end = WEEKDAYS_SHORT[run[-1].weekday()].lower()
            parts.append(f"{start.capitalize()}-{end}")
        else:
            # Single day
            parts.append(WEEKDAYS_SHORT[run[0].weekday()])

    return ", ".join(parts)
