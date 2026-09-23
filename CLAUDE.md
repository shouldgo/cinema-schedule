# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Cinema schedule aggregator for 7 Krakow cinemas. Scrapes repertoire pages, normalizes them into one screening list, and renders a compact markdown digest for Apple Notes.

## Commands

**Run it** — the only entry point:
```bash
python3 cinema.py
```
Prompts for date range and earliest time, writes `schedule.md`.

**Smoke test the whole pipeline** (no test suite exists; this is the check to run after touching a parser):
```bash
python3 -c "
from cinema import fetch_all_screenings
s, st = fetch_all_screenings()
[print(m) for m in st]
print('total', len(s))"
```
Each cinema should report a non-zero count. `cinema.fetch_all_screenings` catches parser exceptions and reports them as status strings rather than raising, so a broken parser surfaces as `⚠ ... parse failed` or a `0 screenings` warning — it will not crash the run.

**Non-interactive run** (useful for diffing output before/after a refactor — pipe the three prompt answers):
```bash
printf '\n\n17:00\n' | python3 cinema.py   # defaults for both dates, 17:00 earliest
```

**Test a single parser** against cached HTML:
```bash
python3 -c "
from fetch import fetch_html
from parsers.kika import parse
r = parse(fetch_html('agrafka'))
print(len(r)); print(r[:3])"
```

**Force a fresh fetch** (bypass the 1-hour cache):
```bash
python3 -c "from fetch import fetch_all; fetch_all(force=True)"
```

## Environment

No dependencies, no venv, no install step — stdlib only, runs on system `python3`. Keep it that way; the zero-setup footprint is the point.

## Architecture

```
cinema.py ─→ fetch.py ─→ cache/*.html
    │
    ├─→ parsers/*.py ─→ [{title, date, time, day}]
    └─→ formatting.py ─→ schedule.md
```

`cinema.py` is the whole front end: prompts, orchestration (`fetch_all_screenings`, `filter_screenings`, `count_results`), and writing the file. Per-cinema scraping logic belongs in `parsers/`, rendering in `formatting.py` — nothing else should need to grow.

**The parser contract.** Every `parsers/<name>.py` exposes `parse(html: str) -> list[dict]` returning dicts with exactly `title`, `date` (ISO `YYYY-MM-DD`), `time` (`HH:MM`), `day` (lowercase Polish weekday). `cinema.fetch_all_screenings` adds the `cinema` key afterward — parsers must not set it. Register a new parser in the `PARSERS` dict in `parsers/__init__.py` (`key -> (display_name, parse_fn)`) and add its URL + source encoding to `fetch.CINEMAS` under the same key; that key joins the two and names the cache file. Two keys may share a URL when one feed covers two venues (`mikro` / `mikro_bronowice`) — each key caches its own copy and its parser filters to its venue.

Downstream sorting and filtering are plain string comparisons on `date` and `time`, so zero-padding is mandatory (`f"{month:02d}"`, `.zfill(2)`).

**Everything is regex, no HTML library.** The stdlib-only footprint is deliberate. Parsers work by slicing HTML between successive anchor matches (KIKA, Paradox) or `re.split` on date separators (Barany), then running field regexes inside each block. The exception is Mikro, whose site renders client-side from a JSON API — its parser uses stdlib `json`, and `cache/mikro*.html` holds JSON despite the extension.

**Caching is central to parser development.** `fetch.fetch_html` returns cached HTML for an hour, so iterating on a regex re-parses the same bytes without hammering the cinema sites. Cache files are always written as UTF-8 regardless of source encoding (Barany is ISO-8859-2), so parsers always receive a `str` decoded from UTF-8.

**Filtering happens once, in `cinema.main`.** `formatting.format_schedule` takes an already-filtered list and only groups and renders it — by title, then cinema, then time, collapsing consecutive dates via `dates.collapse_days` ("pn-śr"). Its `from_date`/`to_date` args feed the header line, not a filter. Don't reintroduce filtering there.

`collapse_days` always returns lowercase; capitalizing the leading weekday is the caller's job, because it depends on where the range lands in a line (see Output Format). `format_schedule` does that with `line[0].upper() + line[1:]` — `str.capitalize()` would lowercase the cinema name at the end of the line.

**One separator, two levels — deliberately.** `collapse_days` joins gapped day runs with `, `, and `format_schedule` joins whole showtimes with `, `, so `pt, wt 20:30, sb 18:00, Barany` is ambiguous on paper: `pt, wt 20:30` is one 20:30 showtime, but parses as a timeless `pt` plus a separate `wt 20:30`. Roughly 9 of 106 cinema lines a week. Left as-is on purpose — a bare weekday with no time is meaningless, so a reader resolves it. Both fixes were rendered on real data and rejected as worse: `/` between gapped runs (`Śr-cz/sb/pn 18:30`) collides visually with the `-` in ranges, and repeating the time per run (`Śr-cz 18:30, sb 18:30, pn 18:30`) is verbose. Don't re-litigate without looking at the rendered output.

## Parser Notes

| Cinema | Key | Structure |
|--------|-----|-----------|
| KIKA | `kika` | FLAT — ISO date embedded in the row's `class` attr |
| Agrafka | `agrafka` | Same booking-system template as KIKA — reuses `parsers/kika.py` verbatim, just fetched from `bilety.kinoagrafka.pl` |
| Mikro | `mikro` | JSON API on `bilety.kinomikro.pl` (not the KIKA template — that parser finds nothing there); keeps `location.id` 3, 13 (Sala Mikro, Mikroffala at Lea 5) |
| Mikro Bronowice | `mikro_bronowice` | Same feed as Mikro, `parsers/mikro.py:parse_bronowice`; keeps `location.id` 8 (Galeria Bronowice) |
| Paradox | `paradox` | DATE-FIRST — `data-date` attr |
| Barany | `baranami` | DATE-FIRST — ISO-8859-2 source encoding |
| Kijów | `kijow` | JS extraction from an embedded data literal |

### Title extraction policy

**Always extract Polish titles** (anchor text), never original titles (the `title` attribute).

Cinemas often carry both: `<a title="Marty Supreme">Wielki Marty</a>`. Using the `title` attr produces duplicate entries when the same film has different original titles across cinemas. All parsers pass titles through `formatting.normalize_title` (`.strip().title()`) — that title-casing is what makes cross-cinema grouping match, so keep it.

### Year inference

Barany omits the year from its markup and reconstructs it. The reconstruction has known failure modes, documented at the code site — start there if dates land in the wrong year. (Mikro's JSON carries full ISO timestamps in Warsaw local time, so it needs none.)

## Output Format

```markdown
# Cinema Schedule: 2026-02-04 → 2026-02-10

**Zaproszenie** ([IMDB](https://www.imdb.com/find/?q=Zaproszenie))
Pn-cz 18:00, pn-cz 20:15, KIKA
Pn-śr 20:15, cz 20:30, Barany
Pn-śr 20:25, cz 18:15, Kijów
---
**Hamnet** ([IMDB](https://www.imdb.com/find/?q=Hamnet)) — pt, wt 20:30, sb 18:00, Barany
---
**La Grazia** ([IMDB](https://www.imdb.com/find/?q=La%20Grazia)) — wt-cz 20:00, KIKA
```

**One line per cinema**, carrying all of that cinema's showtimes. A movie playing at a single cinema collapses onto the title line after an em dash; two or more cinemas get a title line followed by one line each. The title is bold and the IMDb search link is a separate `([IMDB](…))` suffix.

Ordering: cinema lines by that cinema's earliest `(date, time)`; showtimes within a line by the segment's earliest date, ties broken by time (hence `Pn-śr 20:25, cz 18:15` — not sorted by clock time).

`, ` separates both showtimes and gapped day runs, so `pt, wt 20:30` is a single 20:30 showtime on Friday and Tuesday — see the architecture note above for why that collision is intentional.

Capitalization: the leading weekday is capitalized at the start of a cinema line, and stays lowercase after the em dash and for every later segment on a line.
