"""Output formatting for Apple Notes."""

from datetime import date
from urllib.parse import quote

from dates import collapse_days


def normalize_title(title: str) -> str:
    """Convert to title case for consistent display."""
    return title.strip().title()


def format_schedule(
    screenings: list[dict],
    from_date: date,
    to_date: date
) -> str:
    """
    Format screenings as markdown for Apple Notes.

    Input: pre-filtered list of {title, date, time, day, cinema}. Filtering is the
    caller's job; from_date/to_date are used only for the header.
    Output: markdown string
    """
    if not screenings:
        return f"# Cinema Schedule: {from_date} → {to_date}\n\nNo screenings found."

    # Group by movie title
    movies = {}
    for s in screenings:
        title = s["title"]
        if title not in movies:
            movies[title] = []
        movies[title].append(s)

    # For each movie, group screenings by (time, cinema)
    lines = [f"# Cinema Schedule: {from_date} → {to_date}\n"]

    for title in sorted(movies.keys(), key=str.lower):
        # Group by (time, cinema)
        time_cinema_groups = {}
        for s in movies[title]:
            key = (s["time"], s["cinema"])
            if key not in time_cinema_groups:
                time_cinema_groups[key] = []
            time_cinema_groups[key].append(date.fromisoformat(s["date"]))

        # Format each group
        parts = []
        for (time_str, cinema), dates in sorted(time_cinema_groups.items()):
            day_range = collapse_days(dates)
            parts.append(f"{day_range} {time_str}, {cinema}")

        encoded = quote(title)
        title_link = f"[{title}](https://www.imdb.com/find/?q={encoded})"
        if len(parts) == 1:
            lines.append(f"{title_link} — {parts[0]}")
        else:
            lines.append(title_link)
            for part in parts:
                lines.append(part)
        lines.append("---")

    # Remove trailing separator
    if lines and lines[-1] == "---":
        lines.pop()

    return "\n".join(lines)
