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

    lines = [f"# Cinema Schedule: {from_date} → {to_date}\n"]

    for title in sorted(movies.keys(), key=str.lower):
        # Group by cinema, then by time within that cinema
        cinema_times = {}
        for s in movies[title]:
            cinema_times.setdefault(s["cinema"], {}).setdefault(s["time"], []) \
                .append(date.fromisoformat(s["date"]))

        # One line per cinema: every showtime there, earliest date first
        cinema_lines = []
        for cinema, times in cinema_times.items():
            segments = sorted(
                ((min(dates), time_str, f"{collapse_days(dates)} {time_str}")
                 for time_str, dates in times.items())
            )
            line = ", ".join(seg[2] for seg in segments) + f", {cinema}"
            cinema_lines.append((segments[0][:2], line))

        # Cinemas ordered by their earliest (date, time)
        cinema_lines.sort()

        encoded = quote(title)
        title_link = f"**{title}** ([IMDB](https://www.imdb.com/find/?q={encoded}))"
        if len(cinema_lines) == 1:
            # Mid-sentence after the em dash, so the weekday stays lowercase
            lines.append(f"{title_link} — {cinema_lines[0][1]}")
        else:
            lines.append(title_link)
            for _, line in cinema_lines:
                # Not .capitalize(): it would lowercase the cinema name too
                lines.append(line[0].upper() + line[1:])
        lines.append("")

    # Remove trailing blank line
    lines.pop()

    return "\n".join(lines)
