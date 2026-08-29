from typing import List
import polars as pl
from polars import Int32
import plotly.graph_objects as go
import plotly.express as px
from lab.services.kpis import KPIS


class PiramidEtary:
    def __init__(self):
        pass

    def load_data(self, disease, year, uf, mun, sex, age, pop) -> pl.DataFrame:
        kpis_service = KPIS(
            dis_code=disease,
            year=year,
            uf=uf,
            mun=mun,
            age=age,
            sex=sex,
            pop=pop
        )
        return kpis_service.main()

    def prepare_data(self, df: pl.DataFrame, metric: List[str]) -> pl.DataFrame:
        required_cols = ["FAIXA_ETARIA", "SEXO", metric]
        if df.is_empty() or not all(col in df.columns for col in required_cols):
            return pl.DataFrame()

        return (
            df.filter(
                    pl.col("FAIXA_ETARIA").is_not_null(),
                    pl.col("SEXO").is_not_null()
            )
            .filter(pl.col("SEXO").is_in(["M", "F"]))
                .group_by(["FAIXA_ETARIA", "SEXO"])
                .agg(
                    pl.col(metric).mean().alias("VALUE")
                )
                .sort("FAIXA_ETARIA")
                .with_columns([
                    pl.when(pl.col("SEXO") == "M")
                    .then(-pl.col("VALUE"))
                    .otherwise(pl.col("VALUE"))
                    .alias("VALUE_PYRAMID"),
                    pl.col("VALUE").abs().alias("VALUE_ABS")
                ])
        )


    def plot(self, df: pl.DataFrame, metric : str) -> go.Figure:
        if df.is_empty():
            return go.Figure()

        fig = px.bar(
            df.to_pandas(),
            x="VALUE_PYRAMID",
            y="FAIXA_ETARIA",
            color="SEXO",
            orientation='h',
            text="VALUE_ABS",
            title=f"Distribuicao de Faixa Etaria e Sexo ({metric}",
            category_orders={"SEXO": ["M", "F"]},
            labels={"SEXO": "Sexo", "VALUE_PURAMID": "Quantidade", "FAIXA_ETARIA": "Faixa Etaria"}
        )

        fig.update_traces(texttemplate="%{text:,d}", textposition="inside")
        fig.update_xaxes(tickformat="s", zeroline=True)
        fig.update_layout(
            barmode="relative",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        return fig

    def main(self, disease, year, uf, mun, sex, age, pop, metric):
        df_raw = self.load_data(disease, year, uf, mun, sex, age, pop)
        df_prepared = self.prepare_data(df_raw, metric=metric)
        fig = self.plot(df_prepared, metric=metric)
        return fig

if __name__ == "__main__":
    DISEASE_TEST = "CHAG"
    YEAR_TEST = [2020]
    UF_TEST = "MA"
    MUN_TEST = None
    SEX_TEST = None
    AGE_TEST = None
    POP_TEST = None
    METRIC_TEST = "INCIDENCE"
    TOP_N_TEST = 10

    print("=" * 60)
    print(f" Executando teste estático para PiramidEtary ({DISEASE_TEST} - {UF_TEST}/{YEAR_TEST})")
    print("=" * 60)

    renderer = PiramidEtary()
    fig = renderer.main(
        disease=DISEASE_TEST,
        year=YEAR_TEST,
        uf=UF_TEST,
        mun=MUN_TEST,
        sex=SEX_TEST,
        age=AGE_TEST,
        pop=POP_TEST,
        metric=METRIC_TEST,
    )
    fig.show()
