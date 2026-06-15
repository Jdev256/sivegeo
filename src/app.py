import streamlit as st
import pandas as pd
import polars as pl
from lab.core.data_loader import Pysus
from lab.services.kpis import KPIS
from lab.services.indicators import Indicators
from lab.services.indices import Indices
from lab.services.determinantes import Determinantes
from lab.services.distribution import Distribution
from st_pages import add_page_title, get_nav_from_toml

st.write("""
# SIVEGEO LAB
""")

st.set_page_config(layout='wide')

nav = get_nav_from_toml("pages/pages.toml")

pg = st.navigation(nav)
add_page_title(pg)
pg.run()