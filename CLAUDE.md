# CLAUDE.md

Cinema schedule aggregator for 6 Krakow cinemas.

## Usage

**CLI:**
```bash
python3 cinema.py
```
Prompts for date range and time filter, outputs to `schedule.md`.

**GUI (Streamlit):**
```bash
./gui
```
Opens web interface at http://localhost:8501. Press Ctrl+C to stop.

## Structure

```
cinema.py          # CLI entry point
gui.py             # Streamlit web interface
core.py            # Shared logic (fetch, filter, count)
fetch.py           # HTTP fetching with 1-hour cache
formatting.py      # Apple Notes markdown output
dates.py           # Polish dates, day collapsing
parsers/           # One file per cinema
  kika.py
  mikro.py
  agrafka.py
  paradox.py
  baranami.py
  kijow.py
cache/             # HTML cache (gitignored)
.venv/             # Python 3.12 virtualenv (streamlit requires 3.12, not 3.14)
```

## Dependencies

GUI requires streamlit. Setup:
```bash
~/.pyenv/versions/3.12.8/bin/python3 -m venv .venv
source .venv/bin/activate
pip install streamlit
```

## Parser Notes

| Cinema | URL | Parser Type |
|--------|-----|-------------|
| KIKA | bilety.kinokika.pl | FLAT (date in class attr) |
| Mikro | kinomikro.pl | DATE-FIRST (separator divs) |
| Agrafka | kinoagrafka.pl | DATE-FIRST (tables, strip comments) |
| Paradox | kinoparadox.pl | DATE-FIRST (data-date attr) |
| Barany | kinopodbaranami.pl | DATE-FIRST (ISO-8859-2 encoding) |
| Kijów | kupbilet.kijow.pl | JS extraction |

### Title Extraction Policy

**Always extract Polish titles** (anchor text), not original titles (`title` attribute).

Cinemas often display both: `<a title="Marty Supreme">Wielki Marty</a>`. Using `title` attr causes duplicates when the same movie has different original titles across cinemas.

### Agrafka HTML Quirks

The Agrafka HTML has inconsistent structure. When writing regexes for anchor text extraction:

1. **Nested `<b>` tags** — titles often wrapped: `<a href="..."><b>TITLE</b></a>`
2. **Trailing whitespace** — space before closing tag: `<b>TITLE</b> </a>`
3. **Combined pattern** — must handle both: `>\s*(?:<b>)?([^<]+)(?:</b>)?\s*</a>`

Example variations in the wild:
```html
<a href="film.php?...">TITLE</a>
<a href="film.php?..."><b>TITLE</b></a>
<a href="film.php?..."><b>TITLE</b> </a>
<a href="film.php?..."><b>TITLE </b> </a>
```

## Output Format

```markdown
# Cinema Schedule: 2026-02-04 → 2026-02-10

Hamnet
Wt-czw 17:30, KIKA
Wt-czw 19:45, Paradox
---
La Grazia — Wt-czw 20:00, KIKA
```
