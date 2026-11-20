"""Reusable Streamlit views; business rules live in the other modules."""

import base64
import calendar
from html import escape
import sqlite3

import pandas as pd
import streamlit as st

from .assumptions import BUDGET_NOTE, DURATION_NOTE, EXCLUDES, INCLUDES
from .budget import BudgetAssumptions, estimate_budget
from .catalog import comparison_rows, image_credits, photo_path
from .favorites import favorite_ids, remove_favorite, save_favorite
from .models import EXPERIENCE_LEVELS, INTERESTS, Preferences
from .recommender import DEFAULT_WEIGHTS, recommend
from .weather import WeatherError, fetch_forecast


def photo(trek, credits, hero=False):
    path = photo_path(trek.id, credits)
    if path is None:
        st.info(f"Photo unavailable · {trek.name}. Route information remains available.")
        return
    credit = credits[trek.id]
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    height = 320 if hero else 220
    st.html(f'<img src="data:image/jpeg;base64,{data}" alt="{escape(credit["caption"])}" '
            f'style="width:100%;height:{height}px;object-fit:cover;border-radius:14px">')
    st.caption(credit["caption"])
    st.markdown(f'<small>Photo: {escape(credit["author"])} · '
                f'<a href="{escape(credit["source_url"])}">Wikimedia Commons</a> · '
                f'<a href="{escape(credit["license_url"])}">{escape(credit["license"])}</a></small>',
                unsafe_allow_html=True)


def favorite_button(trek, saved, key):
    is_saved = trek.id in saved
    if st.button("Remove favorite" if is_saved else "Save favorite", key=key, width="stretch"):
        try:
            (remove_favorite if is_saved else save_favorite)(trek.id)
            st.rerun()
        except (sqlite3.Error, OSError, ValueError):
            st.error("Could not update favorites. Check that the data folder is writable, then retry.")


def route_details(trek):
    st.write(trek.itinerary_note)
    st.text(trek.cost_note)
    st.write(trek.altitude_note)
    st.markdown("**Place & culture**")
    for highlight in trek.cultural_highlights:
        st.write("• " + highlight)
    st.markdown("**Route considerations**")
    for note in trek.considerations:
        st.write("• " + note)
    st.write("Preferred months: " + ", ".join(calendar.month_abbr[m] for m in trek.preferred_months))
    if trek.elevation_points:
        st.markdown("**Selected landmark elevations**")
        frame = pd.DataFrame(trek.elevation_points).rename(columns={"place": "Landmark", "altitude_m": "Approx. elevation (m)"})
        st.bar_chart(frame.set_index("Landmark"), color="#18796e")
        st.caption("Selected sourced elevations, not a continuous trail profile, daily itinerary, distance scale or acclimatization plan. Optional/alternative landmarks are labeled.")
    for source in trek.sources:
        st.markdown(f"[{source['title']}]({source['url']}) · reviewed {source['accessed']}")
        st.caption(source["supports"])


def trek_card(trek, credits, saved, key, result=None):
    with st.container(border=True):
        photo(trek, credits)
        st.caption(trek.region.upper())
        st.subheader(trek.name)
        if result:
            st.metric("Preference fit / 100", f"{result.score:.0f}")
        st.write(trek.summary)
        st.caption(f"{trek.days_min} days in Nepal · ~USD {trek.cost_min:,.0f}–{trek.cost_max:,.0f} / person")
        st.caption(f"{trek.difficulty} · Highest point ~{trek.max_altitude_m:,} m")
        if result:
            for warning in result.warnings:
                st.warning(warning)
            with st.expander("Why this matches"):
                for reason in result.explanations:
                    st.write("• " + reason)
                st.dataframe(pd.DataFrame([{"Factor": name, "Fit (%)": round(value*100,1),
                    "Weight (%)": round(result.weights[name]*100,1),
                    "Points": round(value*result.weights[name]*100,1)} for name,value in result.factors.items()]),
                    hide_index=True, width="stretch")
        favorite_button(trek, saved, key)
        with st.expander("Explore route · elevations & sources"):
            route_details(trek)


def explore(treks, credits, saved):
    left, right = st.columns([1, 2.4], gap="large")
    with left:
        st.subheader("Find your trail")
        with st.form("preferences"):
            days = st.number_input("Available days in Nepal", 1, 60, 14, key="days", help=DURATION_NOTE)
            budget = st.number_input("Package budget · USD / person", 1, 50000, 1200, step=50, key="budget", help=BUDGET_NOTE)
            experience = st.selectbox("Trekking experience", EXPERIENCE_LEVELS, key="experience")
            month = st.selectbox("Travel month", range(1,13), index=9, format_func=lambda m: calendar.month_name[m], key="month")
            interests = st.multiselect("What draws you to the trail?", INTERESTS,
                                       default=["Mountain views", "Local culture"], key="interests")
            submitted = st.form_submit_button("Find my treks", type="primary", width="stretch")
        if submitted:
            try:
                preferences = Preferences(int(days), float(budget), experience, int(month), tuple(interests))
                recommend(treks, preferences)
                st.session_state["submitted_preferences"] = preferences
            except ValueError as error:
                st.error(str(error))
        with st.expander("Cost & duration assumptions"):
            st.write(DURATION_NOTE)
            st.write(BUDGET_NOTE)
            st.write("Included: " + INCLUDES)
            st.write("Extra: " + EXCLUDES)
            st.caption("Route notes override general inclusions; Everest's listed package includes Lukla flights. Budget estimator extras do not change recommendation inputs.")
    with right:
        preferences = st.session_state.get("submitted_preferences")
        st.caption("PREFERENCE COMPATIBILITY · NOT A SAFETY OR MEDICAL FITNESS ASSESSMENT")
        if preferences is None:
            st.subheader("Six journeys. Your own pace.")
            st.write("Explore the catalog, or submit your preferences for explained rankings.")
            items = [(trek,None) for trek in treks]
        else:
            report = recommend(treks, preferences)
            st.subheader("Your Himalayan shortlist")
            st.caption(f"Submitted: {preferences.days} days · USD {preferences.budget:,.0f} · {preferences.experience} · {calendar.month_name[preferences.month]}. Resubmit to update.")
            items = [(result.trek,result) for result in report.matches]
            if not items:
                st.info("No curated itinerary fits both your time and package budget. Review the exclusions below.")
            if report.excluded:
                with st.expander("Outside your time or budget", expanded=not items):
                    for name, reasons in report.excluded.items():
                        st.write(f"{name}: {' '.join(reasons)}")
        columns = st.columns(2)
        for index,(trek,result) in enumerate(items):
            with columns[index % 2]:
                trek_card(trek,credits,saved,"explore_"+trek.id,result)


def favorites_view(treks, credits, saved):
    st.subheader("Keep the journeys that stay with you")
    st.caption("Saved on this computer in SQLite. Shared by anyone using this local app; no account or cloud sync.")
    selected = [t for t in treks if t.id in saved]
    if not selected:
        st.info("No favorites yet. Save a trek from Explore to build your shortlist.")
    columns = st.columns(3)
    for index,trek in enumerate(selected):
        with columns[index % 3]:
            trek_card(trek,credits,saved,"favorite_"+trek.id)
    unavailable = set(saved) - {t.id for t in treks}
    for trek_id in sorted(unavailable):
        st.warning(f"Saved route currently unavailable: {trek_id}. Your saved record has been retained.")
        if st.button("Remove unavailable favorite", key="orphan_"+trek_id):
            try:
                remove_favorite(trek_id)
                st.rerun()
            except sqlite3.Error:
                st.error("Could not remove this favorite. Please retry.")


def compare_view(treks, credits):
    st.subheader("Different trails, side by side")
    by_id = {t.id:t for t in treks}
    ids = st.multiselect("Compare up to four treks", list(by_id), default=list(by_id)[:2],
                         format_func=lambda key: by_id[key].name, max_selections=4, key="comparison")
    chosen = [by_id[key] for key in ids]
    if not chosen:
        st.info("Select at least one trek to compare.")
        return
    cols = st.columns(len(chosen))
    for col,trek in zip(cols,chosen):
        with col:
            photo(trek,credits)
            st.markdown("**"+trek.name+"**")
    frame = pd.DataFrame(comparison_rows(chosen))
    st.dataframe(frame.set_index("Trek").T, width="stretch")
    st.download_button("Download comparison CSV", frame.to_csv(index=False).encode("utf-8-sig"),
                       file_name="himalayaiq-comparison.csv", mime="text/csv")
    st.bar_chart(pd.DataFrame({"Trek":[t.name for t in chosen],"Approx. maximum altitude (m)": [t.max_altitude_m for t in chosen]}).set_index("Trek"),color="#18796e")
    st.caption("Maximum elevation may be a viewpoint or optional hike, not overnight altitude. See each route's altitude note. Height is not a safety rating.")
    for trek in chosen:
        st.write(f"**{trek.name}:** {trek.altitude_note}")


def budget_view(treks):
    st.subheader("Plan beyond the package")
    st.write("Build an editable USD-per-person scenario. These are your assumptions, not current market quotes.")
    by_id={t.id:t for t in treks}
    route_id=st.selectbox("Budget for a trek",list(by_id),format_func=lambda key:by_id[key].name,key="budget_trek")
    trek=by_id[route_id]
    st.text(trek.cost_note)
    st.caption("Package price starts at the upper listed tier for planning. Extras start at zero because we cannot know your flights, insurance or spending. Enter them before treating this as a trip estimate.")
    a,b,c=st.columns(3)
    with a:
        package=st.number_input("Package price / person",0.0,100000.0,float(trek.cost_max),step=10.0,key="package_"+route_id)
        days=st.number_input("Days for daily extras",1,60,trek.days_min,key="extras_days_"+route_id)
        daily=st.number_input("Daily extras / person",0.0,100000.0,0.0,step=5.0)
        flights=st.number_input("International flights / person",0.0,100000.0,0.0,step=50.0)
    with b:
        visa=st.number_input("Visa / person",0.0,100000.0,0.0)
        insurance=st.number_input("Insurance / person",0.0,100000.0,0.0)
        equipment=st.number_input("Equipment / person",0.0,100000.0,0.0)
        tips=st.number_input("Tips / person",0.0,100000.0,0.0)
    with c:
        nights=st.number_input("Extra nights",0,60,0)
        nightly=st.number_input("Extra night cost / person",0.0,100000.0,0.0)
        contingency=st.number_input("Contingency (%)",0.0,100.0,0.0)
        travelers=st.number_input("Travelers",1,50,1)
    try:
        estimate=estimate_budget(BudgetAssumptions(package,days,daily,flights,visa,insurance,equipment,tips,nights,nightly,contingency,travelers))
    except ValueError as error:
        st.error(str(error));return
    x,y=st.columns(2)
    x.metric("Scenario USD / person",f"{estimate.per_person:,.2f}")
    y.metric("Party total USD",f"{estimate.group_total:,.2f}")
    st.caption("Party total multiplies your per-person assumptions; it does not infer group discounts. Contingency applies to all entered categories.")
    frame=pd.DataFrame([{"Category":k,"USD / person":v} for k,v in estimate.categories.items()]+[{"Category":"Contingency","USD / person":estimate.contingency}])
    st.dataframe(frame,hide_index=True,width="stretch")
    st.download_button("Download budget CSV",frame.to_csv(index=False).encode("utf-8-sig"),file_name="himalayaiq-budget.csv",mime="text/csv")


@st.cache_data(ttl=900,show_spinner=False)
def cached_forecast(latitude,longitude):
    return fetch_forecast(latitude,longitude)


def weather_view(treks):
    st.subheader("Weather, with its place in context")
    by_id={t.id:t for t in treks}
    selected=st.selectbox("Choose a route's weather location",list(by_id),format_func=lambda key:by_id[key].name,key="weather_trek")
    trek=by_id[selected]
    st.write(trek.weather_location)
    st.caption("Upcoming three days in Nepal time, independent of travel month. A settlement forecast does not describe the entire trail, a pass or a summit.")
    if st.button("Load / refresh live forecast",key="load_weather"):
        cached_forecast.clear(trek.latitude,trek.longitude)
        with st.spinner("Contacting Open-Meteo…"):
            try:
                st.session_state["weather_result"]=(selected,cached_forecast(trek.latitude,trek.longitude),None)
            except WeatherError as error:
                st.session_state["weather_result"]=(selected,None,str(error))
    result=st.session_state.get("weather_result")
    if result and result[0]==selected:
        _,forecast,error=result
        if error:
            st.warning(error+" Trek recommendations remain available.")
        else:
            for col,row in zip(st.columns(len(forecast.rows)),forecast.rows):
                with col:
                    with st.container(border=True):
                        st.markdown("**"+row['Date']+"**")
                        low,high=row['Low (°C)'],row['High (°C)']
                        st.write(f"{low if low is not None else '—'} to {high if high is not None else '—'} °C")
                        rain=row['Precipitation (mm)']
                        st.caption(f"Precipitation: {rain if rain is not None else 'unavailable'} mm")
            st.dataframe(pd.DataFrame(forecast.rows),hide_index=True,width="stretch")
            st.caption(f"Retrieved {forecast.fetched_at} · {forecast.timezone} · coordinates {trek.latitude}, {trek.longitude}")
            if forecast.missing_values:
                st.info("Missing values remain blank; they are not zero.")
    st.markdown("Forecasts: [Open-Meteo](https://open-meteo.com/) · Settlement coordinates: [GeoNames](https://www.geonames.org/)")
