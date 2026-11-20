"""HimalayaIQ entry point: python -m streamlit run app.py."""

import sqlite3

import streamlit as st

from himalayaiq.catalog import image_credits
from himalayaiq.database import load_treks
from himalayaiq.favorites import favorite_ids
from himalayaiq.ui import explore, favorites_view, compare_view, budget_view, weather_view

st.set_page_config(page_title="HimalayaIQ · Trails of Nepal", page_icon="🏔️", layout="wide")
st.html("""
<style>
.block-container {max-width:1440px;padding-top:2rem;}
.hero {position:relative;overflow:hidden;border-radius:20px;padding:2.4rem 2.6rem;
       color:white;background:linear-gradient(115deg,#102e40,#145b66);margin-bottom:1.4rem;
       border-bottom:5px solid #bd334b;}
.hero h1 {color:white;font-size:clamp(2.2rem,4vw,3.6rem);margin:0;padding:0;}
.hero p {color:#e0f0f2;max-width:680px;font-size:1.1rem;position:relative;z-index:1;}
.eyebrow {letter-spacing:.12em;font-size:.9rem;font-weight:700;color:#a9e3d4;}
.hero::after {content:"";position:absolute;right:0;bottom:0;width:38%;height:85%;
 background:linear-gradient(150deg,#e9f4f6,#5097a5);opacity:.25;
 clip-path:polygon(0 100%,38% 8%,62% 64%,77% 30%,100% 100%);}
small {font-size:.85rem;color:#334e5b;} small a {color:#126b64;}
@media(max-width:700px){.hero{padding:1.5rem}.hero::after{opacity:.12}}
</style>
<div class="hero"><div class="eyebrow">NEPAL · FROM FOREST PATHS TO HIGH HIMALAYA</div>
<h1>HimalayaIQ</h1><p>Find a trail that speaks to you.<br>Six researched journeys. Local perspectives. Clear reasons behind every match.</p></div>
""")
try:
    treks=load_treks()
except (OSError,ValueError,TypeError,sqlite3.Error) as error:
    st.error("The route catalog could not be loaded. Check data/treks.json and the data folder's write permissions.")
    with st.expander("Technical details"):
        st.code(str(error))
    st.stop()
try:
    saved=favorite_ids()
except (OSError,sqlite3.Error):
    saved=[]
    st.warning("Favorites are temporarily unavailable. You can still explore and compare routes.")
credits=image_credits()
# Keep input widgets alive when their view is not rendered. Button state is excluded.
retained_keys = {"days", "budget", "experience", "month", "interests", "comparison",
                 "budget_trek", "weather_trek"}
for key in list(st.session_state):
    if key in retained_keys or key.startswith(("package_", "extras_days_", "estimate_")):
        st.session_state[key] = st.session_state[key]
page=st.radio("Plan your journey",["Explore","Favorites","Compare","Budget","Weather"],horizontal=True,key="navigation",label_visibility="collapsed")
if page=="Explore": explore(treks,credits,saved)
elif page=="Favorites": favorites_view(treks,credits,saved)
elif page=="Compare": compare_view(treks,credits)
elif page=="Budget": budget_view(treks)
else: weather_view(treks)
st.divider()
st.caption("HimalayaIQ · Thoughtful journeys through Nepal · Compatibility reflects preferences, never safety or medical fitness.")
with st.expander("How we choose and credit our information"):
    st.write("Route facts and selected landmark elevations come from linked operator itineraries. Costs are approximate and party-size dependent. Experience expectations and interest tags are editorial. Confirm current arrangements locally.")
    st.write("Photographs are licensed individually and stored locally. Sources, authors, licenses and captions are available beneath each photograph and in assets/image-credits.json. Some photographs show optional or nearby variants, explicitly identified in their captions.")
    st.write("Initial weights: duration 25%, budget 20%, travel month 15%, interests 20%, experience 20%. Missing interests redistribute their weight. Experience warnings remain independent of scores.")
