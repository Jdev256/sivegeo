import traceback

import streamlit as st
import io
import contextlib
from pysus.online_data.SINAN import list_diseases
from lab.core.data_loader import Pysus
from lab.services.piramid_etary import PiramidEtary
from lab.services.ranking import Ranking
from utils import StreamlitStdoutRedirector
import polars as pl
st.set_page_config(
    page_title="SIVEGEO",
    layout="wide"
)

@st.cache_data(ttl=3600, show_spinner="Carregando lista de municípios...")
def cached_get_muns(uf, year):
    return load.get_muns(uf=uf, year=year)

@st.cache_resource
def init_services():
    return Pysus(), PiramidEtary()

load, service = init_services()

if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "processed_fig" not in st.session_state:
    st.session_state.processed_fig = None
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

uf_map = load.uf_map

st.title("Piramide Etaria")

with st.container(border=True):
    col1, col2, col3, = st.columns(3)

    with col1:
        dis_code = st.selectbox("Doenca", options=list_diseases(), disabled=st.session_state.is_processing)
        year = st.select_slider("Intervalo de Anos",
                                options=list(range(2017, 2026 + 1)),
                                value=(2017, 2020), disabled=st.session_state.is_processing)

    with col2:
        uf = st.selectbox("UF:", uf_map.keys(), disabled=st.session_state.is_processing)

        try:
            df_muns = cached_get_muns(uf=uf, year=year)
        except TimeoutError as e:
            st.error(f"⚠️ Não foi possível carregar os municípios agora: {e}")
            df_muns = pl.DataFrame(schema={"COD_MUN": pl.Int32, "name_muni": pl.Utf8})

        if df_muns.height is not None and df_muns.height > 0:
            mun_map = dict(zip(df_muns["name_muni"], df_muns["COD_MUN"]))
            mun_options = ["ALL"] + list(mun_map.keys())
        else:
            mun_options = ["ALL"]  # Fallback se estiver vazio
            st.warning("Nenhum município encontrado para os parâmetros selecionados.")

        selected_mun = st.selectbox("Municipio", mun_options, disabled=st.session_state.is_processing)
        mun_filter = None if selected_mun == "ALL" else selected_mun

    with col3:

        age_filter = st.slider(
            "Faixa Etaria",
            min_value=0,
            max_value=100,
            value=(0, 100),
            disabled=st.session_state.is_processing
        )
        sex = st.selectbox("Sexo", ["ALL", "M", "F"], disabled=st.session_state.is_processing)
        sex_filter = None if sex == "ALL" else sex
        pop = st.number_input("Populacao minima", min_value=0, value=10000, step=5000,
                              disabled=st.session_state.is_processing)
        metric_input = st.selectbox("Metrica", ["INCIDENCE", "MORTALITY", "LETALITY"], disabled=st.session_state.is_processing)

    st.markdown(
        """
        <div style="
            background-color:#4d0000;
            border:3px solid #ff1s1a;
            border-radius:8px;
            padding: 16px 20px;
            margin-top:8px;
            margin-bottom: 14px;
        ">
        <p style="color:#ffffff; font-size:17px; font-weigth:800; margin: 0 0 8px 0;">
         🚨 ATENÇÃO — NÃO INTERROMPA O PROCESSAMENTO 🚨
        </p>
        <p style="color:#ffdddd; font-size:14.5px; margin:0 0 6px 0; line-height: 1.5;">
            Durante o carregamento nao altere o filtro e nem execute nanhuma acao ate que o resultado apareca na tela. 
            Não recarregue a página (F5) e não navegue para outra página do sistema.
        </p>
        <p style="color:#ffdddd; font-size:14.5px; margin:0; line-height:1.5;">
                ⚠️ <b>Por quê isso importa:</b> o sistema baixa e processa arquivos grandes do DATASUS em segundo plano.
                Se o processamento for interrompido no meio, um arquivo pode ficar <b>parcialmente baixado/corrompido</b>
                no cache do servidor. Nas próximas tentativas com os mesmos filtros, o sistema tentará reaproveitar
                esse arquivo quebrado e pode entrar em <b>carregamento infinito (loop travado)</b>, exigindo reinício
                manual da aplicação para ser corrigido.
            </p>
            <p style="color:#ffffff; font-size:14.5px; margin:10px 0 0 0; font-weight:700;">
                ✅ Ajuste todos os filtros primeiro. Só então clique em Calcular. Depois disso, espere.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    calc = st.button("Calcular Indicadores", type="primary", disabled=st.session_state.is_processing)

    if calc:
        st.session_state.is_processing = True
        st.rerun()

st.write(f"DEBUG: Linhas encontradas para {uf}: {df_muns.height}")

with st.container(border=True):
    log_container = st.container(height=400)
    with log_container:
        log_box = st.empty()

if st.session_state.is_processing:

    custom_stream = StreamlitStdoutRedirector(log_box)

    with contextlib.redirect_stdout(custom_stream):

        st.warning(
            "⏳ Processando... **NÃO interrompa, não mude filtros e não recarregue a página** "
            "até o resultado aparecer. Interromper agora pode corromper o cache e travar o sistema "
            "em carregamento infinito.",
            icon="🚨",
        )

        with st.spinner("Testando conexao com DATASUS"):
            try:
                load = service.load_data(
                    disease=dis_code,
                    year=year,
                    uf=uf,
                    mun=mun_filter,
                    sex=sex_filter,
                    age=age_filter,
                    pop=pop
                )
                df = service.prepare_data(df=load, metric=metric_input)

                fig = service.main(
                    disease=dis_code,
                    year=year,
                    uf=uf,
                    mun=mun_filter,
                    age=age_filter,
                    sex=sex_filter,
                    pop=int(pop),
                    metric=metric_input
                )

                if load is None:
                    st.warning("⚠️ Não foi possível carregar os dados. Motivo: Conexão com o DATASUS falhou")
                    st.info("ℹ️ Verifique o terminal do servidor para ver o log detalhado")

                elif load.height == 0:
                    st.warning("Nenhum registro encontrado")
                    st.info("Verifique o terminal do servidor para mais informacoes")

                else:
                    st.session_state.processed_df = df
                    st.session_state.processed_fig = fig

            except Exception as e:
                st.session_state.processed_df = None
                st.session_state.last_error = f"🚨 Erro crítico: {type(e).__name__} - {e}"
                st.session_state.last_traceback = traceback.format_exc()
            st.session_state.is_processing = False
            st.rerun()

tab1, tab2 = st.tabs(["Grafico", "Tabela"])
if st.session_state.processed_df is not None:
    df_result = st.session_state.processed_df
    fig_result = st.session_state.processed_fig

    st.success("✅ Conexão estabelecida")
    st.success("✅ Dados processados com sucesso!")
    st.metric(label="Total de Linhas Carregadas", value=f"{df_result.height:,}")
    if len(df_result)>0:
        with tab1:
            st.plotly_chart(fig_result)
        with tab2:
            st.dataframe(df_result, use_container_width=True)
    else:
        st.warning("Erro nenhum resultado encontrado")
