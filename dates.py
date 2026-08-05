"""Polish date utilities and day collapsing."""

from datetime import date

POLISH_MONTHS = {
    'stycznia': 1, 'lutego': 2, 'marca': 3, 'kwietnia': 4,
    'maja': 5, 'czerwca': 6, 'lipca': 7, 'sierpnia': 8,
    'września': 9, 'października': 10, 'listopada': 11, 'grudnia': 12
}

WEEKDAYS = ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela']
WEEKDAYS_SHORT = ['pn', 'wt', 'śr', 'cz', 'pt', 'sb', 'nd']


def weekday_name(d: date) -> str:
    """Return Polish weekday name for a date."""
    return WEEKDAYS[d.weekday()]


def collapse_days(dates: list[date]) -> str:
    """
    Collapse consecutive dates into ranges.

    Always lowercase — capitalizing the first weekday is the caller's job, since
    it depends on where the range lands in a line (see formatting.format_schedule).

    Gapped runs join with ", ", the same separator formatting.format_schedule uses
    between whole showtimes, so "pt, wt 20:30" is one 20:30 showtime and not a
    timeless "pt" plus a separate "wt 20:30". Ambiguous on paper, but a bare weekday
    with no time is meaningless, so it resolves on reading — accepted deliberately
    over "/" separators or repeating the time per run, both of which read worse.

    Examples:
        [Mon, Tue, Wed] -> "pn-śr"
        [Mon, Wed, Fri] -> "pn, śr, pt"
        [Mon, Tue, Thu, Fri] -> "pn-wt, cz-pt"
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
        if len(run) == 1:
            parts.append(WEEKDAYS_SHORT[run[0].weekday()])
        else:
            # Range: "pn-śr"
            start = WEEKDAYS_SHORT[run[0].weekday()]
            end = WEEKDAYS_SHORT[run[-1].weekday()]
            parts.append(f"{start}-{end}")

    return ", ".join(parts)
