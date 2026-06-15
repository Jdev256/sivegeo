import streamlit as st
from pysus.online_data.SINAN import list_diseases
from lab.core.data_loader import Pysus
from lab.services.heatmap import HeathMap

@st.cache_resource
def init_services():
    return Pysus(), HeathMap()

load, service = init_services()

uf_map = load.uf_map

st.title("Intensidade por Impacto Territorial")

if "proceseed_df" not in st.session_state:
    st.session_state.processed_df = None
if "processed_fig" not in st.session_state:
    st.session_state.processed_fig = None

with st.container(border=True):
    col1, col2, col3, = st.columns(3)

    with col1:
        dis_code = st.selectbox("Doenca", options=list_diseases())
        year = st.select_slider("Intervalo de Anos", options=list(range(2017, 2025)))
        
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


tab1, tab2 = st.tabs(["Grafico", "Tabela"])

if st.button("Calcular", type="primary"):
    with st.spinner("Processando queries lazy e unificando bases"):

        df = service.prepare_data(
            disease=dis_code, 
            year=year, 
            uf=uf, 
            mun=mun_filter,
            age=age_filter,
            sex=sex_filter,
            pop=int(pop))
        
        fig = service.main(
            disease=dis_code,
            year=year,
            uf=uf,
            mun=mun_filter,
            age=age_filter,
            sex=sex_filter,
            pop=int(pop)
        )

        st.session_state.processed_df = df
        st.session_state.processed_fig = fig

if st.session_state.processed_df is not None:
    df_result = st.session_state.processed_df
    fig_result = st.session_state.processed_fig

    if df.height > 0:
        st.success(f"Dados processados com sucesso! {df.height} encontrados")
        
        with tab1:
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            tab2.dataframe(df, height=250, use_container_width=True)
    else:
        st.warning(f"Nenhum registro encontrado")


        
