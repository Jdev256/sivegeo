import contextlib
import traceback

import streamlit as st
from pysus.online_data.SINAN import list_diseases
from lab.core.data_loader import Pysus
from lab.services.kpis import KPIS
from lab.services.radar import Radar
from utils import StreamlitStdoutRedirector


st.set_page_config(
    page_title="SIVEGEO",
    layout="wide"
)

@st.cache_resource
def init_services():
    return Pysus(), Radar()

load, service = init_services()

if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "processed_fig" not in st.session_state:
    st.session_state.processed_fig = None

uf_map = load.uf_map

with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        dis_code = st.multiselect("Doenca", options=list_diseases())
        year = st.select_slider("Intervalo de Anos", 
                                options=list(range(2017, 2025)))
        
    with col3:
        uf = st.selectbox("UF:", uf_map.keys())

        df_muns = load.get_muns(uf=uf, year=year)
        mun_map = dict(zip(df_muns["name_muni"], df_muns["COD_MUN"]))
        mun_options = ["ALL"] + list(mun_map.keys())
        selected_mun = st.selectbox("MUnicipio", mun_options)
        mun_filter = None if selected_mun == "ALL" else selected_mun

    with col4:

        age_filter = st.select_slider(
            "Faixa Etaria", 
            options=list(range(0, 101)),
            value=(0, 100)
            )
        sex = st.selectbox("Sexo", ["ALL", "M", "F"])
        sex_filter = None if sex == "ALL" else sex
        pop = st.number_input("Populacao minima", min_value=0, value=10000, step=5000)
    
    calc = st.button(
        "Calcular Indicadores",
        type="primary",
    )

with st.container(border=True):
    log_container = st.container(height=400)
    with log_container:
        log_box = st.empty()

if calc:
    if not dis_code:
        st.warning("Selecione pelo menos um agravo")
        st.stop()
    
    custom_stream = StreamlitStdoutRedirector(log_box)
    with contextlib.redirect_stdout(custom_stream):

        with st.spinner("Testando conexao com DATASUS"):
            try:
                df = service.load_data(
                    diseases=dis_code, 
                    year=year, 
                    uf=uf, 
                    mun=mun_filter,
                    age=age_filter,
                    sex=sex_filter,
                    pop=int(pop)
                )
        
                fig = service.main(
                    dis=dis_code,
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
                    st.success("✅ Conexão estabelecida")
                    st.success("✅ Dados processados com sucesso!")
                    st.session_state.processed_df = df
                    st.session_state.processed_fig = fig
            
            except Exception as e:
                st.error(f"🚨 Erro crítico:{type(e).__name__} - {e}")
                st.code(traceback.format_exc(), language="python")
                st.session_state.processed_df = None

tab1, tab2 = st.tabs(["Grafico", "Tabela"])

if st.session_state.processed_df is not None:
    df_result = st.session_state.processed_df
    fig_result = st.session_state.processed_fig

    if len(df_result)>0:
        st.success(f"registros encontrados")

        with tab1:
            st.plotly_chart(fig_result, use_container_width=True)
        with tab2:
            tab2.dataframe(df_result, height=250, use_container_width=True)
    else:
        st.warning("Nenhum Dado encontrado")