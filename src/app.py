import streamlit as st
from pathlib import Path
from st_pages import add_page_title, get_nav_from_toml

# 1. Resolve o caminho absoluto do diretório onde app.py reside
CURRENT_DIR = Path(__file__).parent

# 2. Constrói o caminho para o pages.toml de forma agnóstica ao sistema operacional
# Ajuste o caminho abaixo conforme a sua estrutura real.
# Exemplo: Se pages/ está dentro de src/, fica assim:
PAGES_TOML_PATH = CURRENT_DIR / "pages.toml"

# 3. Fail-fast: Se o arquivo não existir, exploda com clareza antes de quebrar o roteador
if not PAGES_TOML_PATH.exists():
    st.error(f"Erro de configuração: Arquivo de rotas não encontrado em {PAGES_TOML_PATH}")
    st.stop()

# 4. Executa a injeção
nav = get_nav_from_toml(str(PAGES_TOML_PATH))
pg = st.navigation(nav)

add_page_title(pg)
pg.run()