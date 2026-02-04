#!/usr/bin/env python3
"""Streamlit web interface for cinema schedule."""

import streamlit as st
from datetime import date, timedelta, time
from pathlib import Path
from urllib.parse import quote

from core import fetch_all_screenings, filter_screenings, count_results
from formatting import format_schedule
from parsers import PARSERS

OUTPUT_FILE = Path(__file__).parent / "schedule.md"
ALL_CINEMAS = [name for _, (name, _) in PARSERS.items()]

st.set_page_config(page_title="Krakow Cinema", page_icon="🎬", layout="wide")
st.title("🎬 Krakow Cinema Schedule")

# Initialize session state
if "screenings" not in st.session_state:
    st.session_state.screenings = []
    st.session_state.status = []
    st.session_state.fetched = False

# Sidebar: inputs
with st.sidebar:
    st.header("Filters")

    from_date = st.date_input("From date", date.today())
    to_date = st.date_input("To date", date.today() + timedelta(days=6))

    col1, col2 = st.columns(2)
    with col1:
        use_min_time = st.checkbox("Earliest time")
        min_time_val = st.time_input("From", value=time(17, 0), key="min_time", disabled=not use_min_time, label_visibility="collapsed")
    with col2:
        use_max_time = st.checkbox("Latest time")
        max_time_val = st.time_input("To", value=time(22, 0), key="max_time", disabled=not use_max_time, label_visibility="collapsed")

    min_time = min_time_val.strftime("%H:%M") if use_min_time else None
    max_time = max_time_val.strftime("%H:%M") if use_max_time else None

    st.subheader("Cinemas")
    selected_cinemas = []
    for cinema in ALL_CINEMAS:
        if st.checkbox(cinema, value=True, key=f"cinema_{cinema}"):
            selected_cinemas.append(cinema)

    st.divider()

    fetch_clicked = st.button("🔄 Fetch Screenings", type="primary", use_container_width=True)

    # Status messages
    if st.session_state.status:
        st.divider()
        st.caption("Fetch status:")
        for msg in st.session_state.status:
            st.text(msg)

# Fetch on button click
if fetch_clicked:
    with st.spinner("Fetching from all cinemas..."):
        screenings, status = fetch_all_screenings()
        st.session_state.screenings = screenings
        st.session_state.status = status
        st.session_state.fetched = True
    st.rerun()

# Main area
if not st.session_state.fetched:
    st.info("Click **Fetch Screenings** to load the schedule.")
elif not st.session_state.screenings:
    st.error("No screenings found. Check your internet connection.")
else:
    # Apply filters
    cinema_set = set(selected_cinemas) if selected_cinemas else None
    filtered = filter_screenings(
        st.session_state.screenings,
        from_date,
        to_date,
        min_time,
        max_time,
        cinema_set
    )

    # Search box
    search = st.text_input("🔍 Search movies", placeholder="Type to filter...")
    if search:
        search_lower = search.lower()
        filtered = [s for s in filtered if search_lower in s["title"].lower()]

    # Stats
    movie_count, screening_count = count_results(filtered)
    st.info(f"**{movie_count}** movies, **{screening_count}** screenings")

    if not filtered:
        st.warning("No screenings match your filters.")
    else:
        # Group by title
        movies = {}
        for s in filtered:
            title = s["title"]
            if title not in movies:
                movies[title] = []
            movies[title].append(s)

        # Display movies
        for title in sorted(movies.keys(), key=str.lower):
            screenings = movies[title]

            # Group by (time, cinema) for compact display
            time_cinema_groups = {}
            for s in screenings:
                key = (s["time"], s["cinema"])
                if key not in time_cinema_groups:
                    time_cinema_groups[key] = []
                time_cinema_groups[key].append(s)

            with st.expander(f"**{title}** ({len(screenings)} screenings)"):
                for (time_str, cinema), group in sorted(time_cinema_groups.items()):
                    dates = [s["date"] for s in group]
                    days = [s["day"] for s in group]
                    if len(dates) == 1:
                        st.write(f"• {days[0]} {dates[0]} **{time_str}** — {cinema}")
                    else:
                        date_range = f"{days[0]}–{days[-1]}"
                        st.write(f"• {date_range} **{time_str}** — {cinema}")

                encoded = quote(title)
                st.markdown(f"[🔗 Search on IMDB](https://www.imdb.com/find/?q={encoded})")

    # Export button
    st.divider()
    if st.button("📥 Export to schedule.md"):
        output = format_schedule(
            st.session_state.screenings,
            from_date,
            to_date,
            min_time
        )
        OUTPUT_FILE.write_text(output, encoding="utf-8")
        st.success(f"Written to: {OUTPUT_FILE}")
