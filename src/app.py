import streamlit as st
from pathlib import Path
from st_pages import add_page_title, get_nav_from_toml

CURRENT_DIR = Path(__file__).parent

PAGES_TOML_PATH = CURRENT_DIR / "pages.toml"
if not PAGES_TOML_PATH.exists():
    st.error(f"Erro de configuração: Arquivo de rotas não encontrado em {PAGES_TOML_PATH}")
    st.stop()

nav = get_nav_from_toml(str(PAGES_TOML_PATH))
pg = st.navigation(nav)

add_page_title(pg)
pg.run()