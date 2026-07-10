import polars as pl
import polars.selectors as cs
import plotly.graph_objects as go
import plotly.io as pio
import geobr

from lab.services.kpis import KPIS
from lab.core.data_loader import Pysus

class HeatMap:
    def __init__(self):
        self.load = Pysus()

    def load_data(self, disease, year, uf, mun, sex, age, pop) -> pl.DataFrame:
        load = KPIS(dis_code=disease, uf=uf, year=year, mun=mun, sex=sex, age=age, pop=pop)
        return load.main()
    
    def prepare_data(self, disease, year, uf, mun, sex, age, pop, top_n: int=20,):
        df = self.load_data(disease=disease, uf=uf, year=year, mun=mun, sex=sex, age=age, pop=pop)
        
        if df.height == 0:
            return df
        
        return (
            df.select("name_muni","INCIDENCE","MORTALITY", "LETALITY")
            .filter(pl.col("name_muni").is_not_null())
            .sort("INCIDENCE", descending=True)
            .head(top_n)
        )
    
    def _min_max_scale(self, series: pl.Series) -> list:
        s_min = series.min()
        s_max = series.max()
        if s_min == s_max or s_min is None or s_max is None:
            return [0.5] * len(series)
        return ((series - s_min) / (s_max - s_min)).to_list()
    
    def plot(self, df: pl.DataFrame) -> go.Figure:
        fig = go.Figure()

        if df.height == 0:
            fig.update_layout(title="Nenhum dato")
            return fig

        #casos = df["TOTAL_CASES"].to_list()
        #obitos = df["TOTAL_DEATHS"].to_list()
        #matrix = [casos, obitos]

        inc = df["INCIDENCE"].to_list()
        mort = df["MORTALITY"].to_list()
        let = df["LETALITY"].to_list()
        matrix = [inc, mort, let]

        incs = self._min_max_scale(df["INCIDENCE"])
        morts = self._min_max_scale(df["MORTALITY"])
        lets = self._min_max_scale(df["LETALITY"])
        matrixs = [incs, morts, lets]

        fig.add_trace(
                go.Heatmap(
                    x=df["name_muni"].to_list(),
                    y=["Incidência (100k hab)", "Mortalidade (100k hab)", "Letalidade (%)"],
                    z=matrixs,
                    coloraxis="coloraxis",
                    text=matrix,
                    texttemplate="%{text:.2f}",
                    textfont={"size": 12},
                    hovertemplate=(
                    "<b>Municipio:</b> %{x}<br>"
                    "<b>Indicador:</b> %{y}<br>"
                    "<b>Valor:</b> %{z}<extra></extra>"
                    )
                )
            )

        fig.update_layout(
            height=500,
            width=900,
            coloraxis=dict(
                colorscale="YlOrRd",
                colorbar=dict(
                    title="Intensidade<br>Relativa", 
                    thickness=15,
                    tickvals=[0, 0.5, 1],
                    ticktext=["min","medium", "max"]
                    )
            ),
            title=dict(
                text="Top Municipios por Impacto Epidemiologico",
                font=dict(size=18, color="black"),
                x=0.02
            ),
            xaxis=dict(
                tickangle=-45,
                side="top",
                tickfont=dict(color="black", size=11),
                gridcolor="rgba(0,0,0, 0.05)"
            ),
            yaxis=dict(
                tickfont=dict(color="black", size=12),
                gridcolor="rgba(0,0,0, 0.05)"
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=150, r=50, t=100, b=100)
        )

        return fig
    
    def main(self, disease, year, uf, mun, sex, age, pop):
        df = self.prepare_data(disease=disease, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)
        fig = self.plot(df)
        return fig
    
if __name__ == "__main__":
    renderer = HeatMap()
    fig =  renderer.main(disease="CHAG", year=2020, uf="MA", mun=None, sex=None, age=None, pop=None)
    fig.show()