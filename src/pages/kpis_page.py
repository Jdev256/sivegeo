import contextlib

import streamlit as st
from pysus.online_data.SINAN import list_diseases
from lab.core.data_loader import Pysus
from lab.services.kpis import KPIS
from utils import StreamlitStdoutRedirector

st.set_page_config(
    page_title="SIVEGEO",
    layout="wide"
)

@st.cache_resource
def init_services():
    return Pysus()

load = init_services()

if "processed_df" not in st.session_state:
    st.session_state.processed_df = None

uf_map = load.uf_map

st.title("Kpis - Indicadores Estrategicos")

with st.container(border=True):
    col1, col2, col3, = st.columns(3)

    with col1:
        dis_code = st.selectbox("Doenca", options=list_diseases())
        year = st.select_slider("Intervalo de Anos", 
                                options=list(range(2017, 2026 + 1)),
                                value=(2017, 2026)
                                )
        
    with col2:
        uf = st.selectbox("UF:", uf_map.keys())

        df_muns = load.get_muns(uf=uf, year=year)
        mun_map = dict(zip(df_muns["name_muni"], df_muns["COD_MUN"]))
        mun_options = ["ALL"] + list(mun_map.keys())
        selected_mun = st.selectbox("MUnicipio", mun_options)
        mun_filter = None if selected_mun == "ALL" else selected_mun

    with col3:

        age_filter = st.select_slider(
            "Faixa Etaria", 
            options=list(range(0, 101)),
            value=(0, 100)
            )
        sex = st.selectbox("Sexo", ["ALL", "M", "F"])
        sex_filter = None if sex == "ALL" else sex
        pop = st.number_input("Populacao minima", min_value=0, value=10000, step=5000)

    calc = st.button("Calcular KPIS", type="primary")

with st.container(border=True):
    log_container = st.container(height=400)
    with log_container:
        log_box = st.empty()

if calc:
    custom_stream = StreamlitStdoutRedirector(log_box)
    with contextlib.redirect_stdout(custom_stream):

        with st.spinner("Processando queries lazy e unificando bases"):
            try:
                instance = KPIS(dis_code=dis_code, year=year, uf=uf, mun=mun_filter, age=age_filter, sex=sex_filter, pop=pop)
                df = instance.main()

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
                st.session_state.processed_df = None

if st.session_state.processed_df is not None:
    df_result = st.session_state.processed_df

    st.success("✅ Conexão estabelecida")
    st.success("✅ Dados processados com sucesso!")
    st.metric(label="Total de Linhas Carregadas", value=f"{df_result.height:,}")
    st.dataframe(df_result, use_container_width=True)