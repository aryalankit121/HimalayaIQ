"""Run with: python -m streamlit run app.py"""

import calendar
import sqlite3

import pandas as pd
import streamlit as st

from himalayaiq.assumptions import BUDGET_NOTE, DURATION_NOTE, EXCLUDES, INCLUDES
from himalayaiq.database import load_treks
from himalayaiq.models import EXPERIENCE_LEVELS, INTERESTS, Preferences
from himalayaiq.recommender import DEFAULT_WEIGHTS, recommend
from himalayaiq.weather import WeatherError, fetch_forecast

st.set_page_config(page_title="HimalayaIQ · Smart Nepal Trek Finder", page_icon="🏔️", layout="wide")
st.html("""
<style>
.block-container {max-width: 1240px; padding-top: 2rem;}
.hero {position:relative; overflow:hidden; border-radius:20px; padding:2.4rem;
       color:#fff; background:linear-gradient(115deg,#102e40,#145b66); margin-bottom:1.5rem;}
.hero h1 {color:white; font-size:clamp(2rem,4vw,3.2rem); margin:0; padding:0;}
.hero p {color:#d8eff1; max-width:640px; font-size:1.1rem;}
.eyebrow {letter-spacing:.16em; font-size:.85rem; font-weight:700; color:#9fe1d5;}
.mountains {position:absolute; right:0; bottom:0; width:42%; opacity:.22; pointer-events:none;}
.hero::after {content:""; position:absolute; right:0; bottom:0; width:38%; height:85%;
 background:linear-gradient(150deg,#dceef1,#4a94a2); opacity:.18; pointer-events:none;
 clip-path:polygon(0 100%,38% 8%,62% 64%,77% 30%,100% 100%);}
@media(max-width:700px){.hero{padding:1.5rem}.mountains{width:65%;opacity:.12}}
</style>
<div class="hero">
<svg class="mountains" viewBox="0 0 500 230" aria-hidden="true">
<path d="M0 230L160 20 270 160 355 55 500 230Z" fill="#94c9d6"/>
<path d="M105 92L160 20 219 95 171 74 149 83 135 65Z" fill="white"/>
<path d="M295 126L355 55 407 118 364 102 343 114 330 91Z" fill="white"/>
<path d="M25 230L235 113 350 230Z" fill="#308c91"/>
</svg>
<div class="eyebrow">NEPAL · FIND YOUR NEXT TRAIL</div>
<h1>HimalayaIQ</h1>
<p>Big mountains. A journey that fits you.<br>Compare three curated treks, with clear reasons behind every match.</p>
</div>
""")


@st.cache_data(ttl=900, show_spinner=False)
def cached_forecast(latitude: float, longitude: float):
    return fetch_forecast(latitude, longitude)


try:
    treks = load_treks()
except (OSError, ValueError, TypeError, sqlite3.Error) as error:
    st.error("The trek dataset could not be loaded. Check data/treks.json and folder write permissions.")
    with st.expander("Technical details"):
        st.code(str(error))
    st.stop()

left, right = st.columns([1, 2.1], gap="large")
with left:
    st.subheader("Your next adventure")
    with st.form("preferences"):
        days = st.number_input("Available days in Nepal", min_value=1, max_value=60, value=14, help=DURATION_NOTE)
        budget = st.number_input("Package budget · USD / person", min_value=1, max_value=50000, value=1200, step=50, help=BUDGET_NOTE)
        experience = st.selectbox("Trekking experience", EXPERIENCE_LEVELS, help="Beginner: new to multiday treks. Intermediate: some multiday trekking. Experienced: extensive multiday trekking. These are self-reported preferences.")
        month = st.selectbox("Travel month", range(1, 13), index=9, format_func=lambda value: calendar.month_name[value])
        interests = st.multiselect("What draws you to the trail?", INTERESTS, default=["Mountain views", "Local culture"])
        submitted = st.form_submit_button("Find my treks", type="primary", width="stretch")
    with st.expander("What's included in these estimates?"):
        st.write(DURATION_NOTE)
        st.write(BUDGET_NOTE)
        st.markdown(f"**Included:** {INCLUDES}")
        st.markdown(f"**Extra:** {EXCLUDES}")
    st.caption("CIS 3400 · Deliverable 2 prototype\n\nThree curated profiles · No booking required")

if submitted:
    preferences = Preferences(int(days), float(budget), experience, int(month), tuple(interests))
    try:
        recommend(treks, preferences)
        st.session_state["submitted_preferences"] = preferences
    except ValueError as error:
        st.error(str(error))

with right:
    st.caption("PREFERENCE COMPATIBILITY · NOT A TREKKING SAFETY ASSESSMENT")
    preferences = st.session_state.get("submitted_preferences")
    if preferences is None:
        st.subheader("Three paths into the Himalayas")
        st.write("Choose your preferences and select **Find my treks** to see personalized rankings.")
        for trek in treks:
            with st.container(border=True):
                st.markdown(f"### {trek.name}")
                st.write(trek.summary)
                st.caption(f"{trek.days_min} days in Nepal · Approx. USD {trek.cost_min:,.0f}–{trek.cost_max:,.0f} / person · {trek.difficulty}")
    else:
        report = recommend(treks, preferences)
        st.subheader("Your trail shortlist")
        st.caption(f"Submitted preferences: {preferences.days} days · USD {preferences.budget:,.0f} package budget · "
                   f"{preferences.experience} · {calendar.month_name[preferences.month]}. Edit and submit again to update.")
        if not report.matches:
            st.info("No curated itinerary fits both your time and package budget. Review the reasons below and adjust your preferences if appropriate.")
        for rank, result in enumerate(report.matches, start=1):
            trek = result.trek
            with st.container(border=True):
                title, score = st.columns([3, 1])
                title.caption(f"MATCH {rank:02d} · {trek.region.upper()}")
                title.markdown(f"### {trek.name}")
                score.metric("Fit / 100", f"{result.score:.0f}")
                st.write(trek.summary)
                st.caption(f"{trek.days_min} days · Approx. USD {trek.cost_min:,.0f}–{trek.cost_max:,.0f} per person · "
                           f"{trek.difficulty} · Up to ~{trek.max_altitude_m:,} m")
                for warning in result.warnings:
                    st.warning(warning)
                with st.expander("Why this matches · score breakdown"):
                    for explanation in result.explanations:
                        st.write(f"• {explanation}")
                    st.dataframe(pd.DataFrame([{
                        "Factor": key, "Compatibility (%)": round(value * 100, 1),
                        "Weight (%)": round(result.weights[key] * 100, 1),
                        "Points / 100": round(value * result.weights[key] * 100, 1),
                    } for key, value in result.factors.items()]), hide_index=True, width="stretch")
                with st.expander("Route details & sources"):
                    st.write(trek.itinerary_note)
                    st.text(trek.cost_note)
                    st.write(trek.altitude_note)
                    st.write("Preferred months: " + ", ".join(calendar.month_abbr[m] for m in trek.preferred_months))
                    st.caption("Experience expectations and interest tags are editorial classifications, not certified assessments.")
                    for source in trek.sources:
                        st.markdown(f"[{source['title']}]({source['url']}) · reviewed {source['accessed']}")
                        st.caption(source["supports"])
        if report.matches:
            st.markdown("### Compare your matches")
            st.dataframe(pd.DataFrame([{
                "Trek": r.trek.name, "Compatibility / 100": round(r.score, 1),
                "Days in Nepal": r.trek.days_min,
                "Approx. package USD": f"{r.trek.cost_min:,.0f}–{r.trek.cost_max:,.0f}",
                "Difficulty": r.trek.difficulty, "Approx. max altitude (m)": r.trek.max_altitude_m,
            } for r in report.matches]), hide_index=True, width="stretch")
        if report.excluded:
            with st.expander("Routes outside your time or budget", expanded=not report.matches):
                for name, reasons in report.excluded.items():
                    st.markdown(f"**{name}:** {' '.join(reasons)}")

st.divider()
weather_col, method_col = st.columns([1.5, 1], gap="large")
with weather_col:
    st.subheader("A look at the weather")
    selected_id = st.selectbox("Choose a route's regional weather location", [t.id for t in treks],
                               format_func=lambda value: next(t.name for t in treks if t.id == value))
    selected = next(t for t in treks if t.id == selected_id)
    st.write(selected.weather_location)
    st.caption("Upcoming 3-day forecast, independent of your travel month. These lower-elevation locations do not represent trail or summit conditions.")
    if st.button("Load / refresh live forecast"):
        # Clear this location only; never substitute example data after a failure.
        cached_forecast.clear(selected.latitude, selected.longitude)
        with st.spinner("Contacting Open-Meteo…"):
            try:
                forecast = cached_forecast(selected.latitude, selected.longitude)
                st.session_state["weather_result"] = (selected.id, forecast, None)
            except WeatherError as error:
                st.session_state["weather_result"] = (selected.id, None, str(error))
    weather_result = st.session_state.get("weather_result")
    if weather_result and weather_result[0] == selected.id:
        _, forecast, error = weather_result
        if error:
            st.warning(error + " Trek recommendations remain available.")
        else:
            st.dataframe(pd.DataFrame(forecast.rows), hide_index=True, width="stretch")
            st.caption(f"Retrieved {forecast.fetched_at} · Forecast timezone: {forecast.timezone} · "
                       f"Requested coordinates: {selected.latitude}, {selected.longitude}")
            if forecast.missing_values:
                st.info("Some forecast values are unavailable; blank cells are not zero.")
    st.markdown("Weather: [Open-Meteo](https://open-meteo.com/) · Locations: [GeoNames](https://www.geonames.org/)")
with method_col:
    st.subheader("Clear reasons. No black box.")
    st.write("We filter by available days and minimum estimated package cost, then rank preference compatibility.")
    st.caption(" · ".join(f"{key} {value:.0%}" for key, value in DEFAULT_WEIGHTS.items()))
    st.write("Experience warnings are independent of the total score. A high score does not establish safety or readiness for altitude.")
    st.caption("Curated estimates reviewed November 19, 2026. Confirm current arrangements, conditions, and prices with local providers.")
