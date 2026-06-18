import streamlit as st
from lab.services.indicators import Indicators
from pysus.online_data.SINAN import list_diseases

from lab.core.data_loader import Pysus
from lab.services.historic_evolution import HistoricEvolution

@st.cache_resource
def init_services():
    return Pysus(), HistoricEvolution()

load, service = init_services()

if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "processed_fig" not in st.session_state:
    st.session_state.processed_fig = None

with st.container(border=True):
    col1, col2, col3, = st.columns(3)

    with col1:
        dis_code = st.selectbox("Doenca", options=list_diseases())
        year = st.select_slider(
            "Intervalo de Anos", 
            options=list(range(2010, 2026 + 1)),
            value=(2020, 2025)
            )
    with col2:
        uf = st.selectbox("UF:", load.uf_map.keys())

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


tab1, tab2 = st.tabs(["Grafico", "Tabela"])

if st.button("Calcular"):
    with st.spinner("Calculando e unificando bases"):
        load = service.load_data(
            dis_code=dis_code,
            year=year,
            uf=uf,
            mun=mun_filter,
            sex=sex_filter,
            age=age_filter,
            pop=pop
        )
        df = service.prepare_data(df=load, metric=["INCIDENCE", "MORTALITY", "LETALITY"])

        fig = service.main(
            d=dis_code,
            y=year,
            uf=uf,
            mun=mun_filter,
            sex=sex_filter,
            age=age_filter,
            pop=pop,
            metric=["INCIDENCE", "MORTALITY", "LETALITY"]
        )

        st.session_state.processed_df = df
        st.session_state.processed_fig = fig

if st.session_state.processed_df is not None:
    df_result = st.session_state.processed_df
    fig_result = st.session_state.processed_fig

    if len(df_result)>0:
        st.success(f"{df} registros encontrados")

        with tab1:
            st.plotly_chart(fig_result)
        with tab2:
            tab2.dataframe(df_result)
    else:
        st.warning("Erro nenhum resultado encontrado")