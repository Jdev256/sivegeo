from typing import List

from lab.core.data_loader import Pysus
import polars as pl
import plotly.express as px
from lab.services.kpis import KPIS

class Ranking:
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

    def prepare_data(self, df: pl.DataFrame, metric: List[str], top_n: int = 10) -> pl.DataFrame:
        if df.is_empty() or df.filter(pl.col("METRIC").is_not_nan()):
            return pl.DataFrame()
        return (
            df.filter(pl.col("name_muni").is_not_null())
            .group_by("name_muni")
            .agg([
                pl.col("TOTAL_CASES").sum(),
                pl.col("TOTAL_DEATHS").sum(),
                pl.col("POPULACAO").max(),
                pl.col(metric).mean().alias("metric")
            ])
            .sort(metric, descending=True)
            .head(top_n)
            .sort(metric, descending=False)
        )

    def plot(self, df: pl.DataFrame, metric: str) -> px.bar:
        fig = px.bar(
            df.to_pandas(),
            x=metric,
            y="name_muni",
            orientation="h",
            text=metric,
            title=f"Top Municipios por {metric}"
        )
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig

    def main(self, disease, year, uf, mun, sex, age, pop, metric, top_n=10):
        df_raw = self.load_data(disease, year, uf, mun, sex, age, pop)
        df_prepared = self.prepare_data(df_raw, metric=metric, top_n=top_n)
        fig = self.plot(df_prepared, metric=metric)
        return fig

if __name__ == "__main__":
    DISEASE_TEST = "CHAG"
    YEAR_TEST = [2017,2020]
    UF_TEST = "MA"
    MUN_TEST = None
    SEX_TEST = None
    AGE_TEST = None
    POP_TEST = None
    METRIC_TEST = "INCIDENCE"
    TOP_N_TEST = 10

    print("=" * 60)
    print(f" Executando teste estático para RankingView ({DISEASE_TEST} - {UF_TEST}/{YEAR_TEST})")
    print("=" * 60)

    renderer = Ranking()
    fig = renderer.main(
        disease=DISEASE_TEST,
        year=YEAR_TEST,
        uf=UF_TEST,
        mun=MUN_TEST,
        sex=SEX_TEST,
        age=AGE_TEST,
        pop=POP_TEST,
        metric=METRIC_TEST,
        top_n=TOP_N_TEST
    )
    fig.show()

