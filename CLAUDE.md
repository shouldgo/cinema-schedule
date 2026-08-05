# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Cinema schedule aggregator for 6 Krakow cinemas. Scrapes repertoire pages, normalizes them into one screening list, and renders a compact markdown digest for Apple Notes.

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
from parsers.agrafka import parse
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

**The parser contract.** Every `parsers/<name>.py` exposes `parse(html: str) -> list[dict]` returning dicts with exactly `title`, `date` (ISO `YYYY-MM-DD`), `time` (`HH:MM`), `day` (lowercase Polish weekday). `cinema.fetch_all_screenings` adds the `cinema` key afterward — parsers must not set it. Register a new parser in the `PARSERS` dict in `parsers/__init__.py` (`key -> (display_name, parse_fn)`) and add its URL + source encoding to `fetch.CINEMAS` under the same key; that key joins the two and names the cache file.

Downstream sorting and filtering are plain string comparisons on `date` and `time`, so zero-padding is mandatory (`f"{month:02d}"`, `.zfill(2)`).

**Everything is regex, no HTML library.** The stdlib-only footprint is deliberate. Parsers work by slicing HTML between successive anchor matches (KIKA, Paradox) or `re.split` on date separators (Mikro, Agrafka, Barany), then running field regexes inside each block.

**Caching is central to parser development.** `fetch.fetch_html` returns cached HTML for an hour, so iterating on a regex re-parses the same bytes without hammering the cinema sites. Cache files are always written as UTF-8 regardless of source encoding (Barany is ISO-8859-2), so parsers always receive a `str` decoded from UTF-8.

**Filtering happens once, in `cinema.main`.** `formatting.format_schedule` takes an already-filtered list and only groups and renders it — by title, then by `(time, cinema)`, collapsing consecutive dates via `dates.collapse_days` ("Pn-śr"). Its `from_date`/`to_date` args feed the header line, not a filter. Don't reintroduce filtering there.

## Parser Notes

| Cinema | Key | Structure |
|--------|-----|-----------|
| KIKA | `kika` | FLAT — ISO date embedded in the row's `class` attr |
| Mikro | `mikro` | DATE-FIRST — `repertoire-separator` divs |
| Agrafka | `agrafka` | DATE-FIRST — tables; strip HTML comments first |
| Paradox | `paradox` | DATE-FIRST — `data-date` attr |
| Barany | `baranami` | DATE-FIRST — ISO-8859-2 source encoding |
| Kijów | `kijow` | JS extraction from an embedded data literal |

### Title extraction policy

**Always extract Polish titles** (anchor text), never original titles (the `title` attribute).

Cinemas often carry both: `<a title="Marty Supreme">Wielki Marty</a>`. Using the `title` attr produces duplicate entries when the same film has different original titles across cinemas. All parsers pass titles through `formatting.normalize_title` (`.strip().title()`) — that title-casing is what makes cross-cinema grouping match, so keep it.

### Year inference

Mikro and Barany omit the year from their markup and reconstruct it. Both reconstructions have known failure modes, documented at the code sites — start there if dates land in the wrong year.

### Agrafka HTML quirks

Markup is inconsistent enough that anchor-text regexes need to tolerate several `<b>`/whitespace variants; see the comment above the title regex in `parsers/agrafka.py`. The page also carries a large block of stale data inside HTML comments, which `parse` strips before anything else.

## Output Format

```markdown
# Cinema Schedule: 2026-02-04 → 2026-02-10

[Hamnet](https://www.imdb.com/find/?q=Hamnet)
Wt-czw 17:30, KIKA
Wt-czw 19:45, Paradox
---
[La Grazia](https://www.imdb.com/find/?q=La%20Grazia) — Wt-czw 20:00, KIKA
```
Single-group movies go on one line with an em dash; multi-group movies get a title line followed by one line per `(time, cinema)`. Titles link to an IMDb search.
