import traceback

import streamlit as st
import io
import contextlib
from pysus.online_data.SINAN import list_diseases
from lab.core.data_loader import Pysus
from lab.services.indicators import Indicators
from utils import StreamlitStdoutRedirector


st.set_page_config(
    page_title="SIVEGEO",
    layout="wide"
)

@st.cache_resource
def init_services():
    return Pysus() , Indicators()

load, service = init_services()

if "processed_df" not in st.session_state:
    st.session_state.processed_df = None

uf_map = load.uf_map

st.title("Indicadores")

#filter_col,console_col = st.columns([2, 1])

with st.container(border=True):
    col1, col2, col3, = st.columns(3)

    with col1:
        dis_code = st.selectbox("Doenca", options=list_diseases())
        year = st.select_slider("Intervalo de Anos", 
                                options=list(range(2017, 2026 + 1)), 
                                value=(2017,2020))
        
    with col2:
        uf = st.selectbox("UF:", uf_map.keys())

        df_muns = load.get_muns(uf=uf, year=year)
        
        if df_muns.height is not None and df_muns.height> 0:
            mun_map = dict(zip(df_muns["name_muni"], df_muns["COD_MUN"]))
            mun_options = ["ALL"] + list(mun_map.keys())
        else:
            mun_options = ["ALL"] # Fallback se estiver vazio
            st.warning("Nenhum município encontrado para os parâmetros selecionados.")
            
        selected_mun = st.selectbox("Municipio", mun_options)
        mun_filter = None if selected_mun == "ALL" else selected_mun

    with col3:

        age_filter = st.slider(
            "Faixa Etaria", 
            min_value=0,
            max_value=100,
            value=(0, 100)
            )
        sex = st.selectbox("Sexo", ["ALL", "M", "F"])
        sex_filter = None if sex == "ALL" else sex
        pop = st.number_input("Populacao minima", min_value=0, value=10000, step=5000)

    calc = st.button(
        "Calcular Indicadores",
        type="primary",
    )

st.write(f"DEBUG: Linhas encontradas para {uf}: {df_muns.height}")


with st.container(border=True):
    log_container = st.container(height=400)
    with log_container:
        log_box = st.empty()

if calc:
    
    custom_stream = StreamlitStdoutRedirector(log_box)

    with contextlib.redirect_stdout(custom_stream):

        with st.spinner("Testando conexao com DATASUS"):
            try:
                df = service.main(
                    disease=dis_code,
                    year=year,
                    uf=uf,
                    mun=mun_filter,
                    age=age_filter,
                    sex=sex_filter,
                    pop=int(pop)
                )
                
                if df is None:
                    st.warning("⚠️ Não foi possível carregar os dados. Motivo: Conexão com o DATASUS falhou")
                    st.info("ℹ️ Verifique o terminal do servidor para ver o log detalhado")
                
                elif df.height == 0:
                    st.warning("Nenhum registro encontrado")
                    st.info("Verifique o terminal do servidor para mais informacoes")
                
                else:
                    st.session_state.processed_df = df
            
            except Exception as e:
                st.error(f"🚨 Erro crítico:{type(e).__name__} - {e}")
                st.code(traceback.format_exc(), language="python")
                st.session_state.processed_df = None

if st.session_state.processed_df is not None:
    df_result = st.session_state.processed_df
    
    st.success("✅ Conexão estabelecida")
    st.success("✅ Dados processados com sucesso!")
    st.metric(label="Total de Linhas Carregadas", value=f"{df_result.height:,}")
    st.dataframe(df_result, use_container_width=True)