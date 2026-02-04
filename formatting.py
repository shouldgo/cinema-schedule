"""Output formatting for Apple Notes."""

from datetime import date
from dates import collapse_days


def normalize_title(title: str) -> str:
    """Convert to title case for consistent display."""
    return title.strip().title()


def format_schedule(
    all_screenings: list[dict],
    from_date: date,
    to_date: date,
    min_time: str | None = None
) -> str:
    """
    Format screenings as markdown for Apple Notes.

    Input: list of {title, date, time, day, cinema}
    Output: markdown string
    """
    # Filter by date range and min time
    filtered = []
    for s in all_screenings:
        try:
            d = date.fromisoformat(s["date"])
        except ValueError:
            continue

        if d < from_date or d > to_date:
            continue

        if min_time and s["time"] < min_time:
            continue

        filtered.append(s)

    if not filtered:
        return f"# Cinema Schedule: {from_date} → {to_date}\n\nNo screenings found."

    # Group by movie title
    movies = {}
    for s in filtered:
        title = s["title"]
        if title not in movies:
            movies[title] = []
        movies[title].append(s)

    # For each movie, group screenings by (time, cinema)
    lines = [f"# Cinema Schedule: {from_date} → {to_date}\n"]

    for title in sorted(movies.keys(), key=str.lower):
        screenings = movies[title]

        # Group by (time, cinema)
        time_cinema_groups = {}
        for s in screenings:
            key = (s["time"], s["cinema"])
            if key not in time_cinema_groups:
                time_cinema_groups[key] = []
            time_cinema_groups[key].append(date.fromisoformat(s["date"]))

        # Format each group
        parts = []
        for (time_str, cinema), dates in sorted(time_cinema_groups.items()):
            day_range = collapse_days(dates)
            parts.append(f"{day_range} {time_str}, {cinema}")

        if len(parts) == 1:
            lines.append(f"{title} — {parts[0]}")
        else:
            lines.append(title)
            for part in parts:
                lines.append(part)
        lines.append("---")

    # Remove trailing separator
    if lines and lines[-1] == "---":
        lines.pop()

    return "\n".join(lines)
