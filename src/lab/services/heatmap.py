import polars as pl
import polars.selectors as cs
import plotly.graph_objects as go
import plotly.io as pio
import geobr

from lab.services.indicators import Indicators
from lab.core.data_loader import Pysus

class HeathMap:
    def __init__(self):
        self.load = Pysus()
        self.indicators = Indicators()

    def load_data(self, disease, year, uf, mun, sex, age, pop) -> pl.DataFrame:
        load = self.indicators.main(disease=disease, uf=uf, year=year, mun=mun, sex=sex, age=age, pop=pop)
        return load
    
    def prepare_data(self, disease, year, uf, mun, sex, age, pop, top_n: int=20,):
        load_data = self.load_data(disease=disease, uf=uf, year=year, mun=mun, sex=sex, age=age, pop=pop)
        df = (
            load_data.select("name_muni","TOTAL_CASES","TOTAL_DEATHS")
            .sort("TOTAL_CASES", descending=True)
            .head(top_n)
        )
        return df
    
    def plot(self, df: pl.DataFrame) -> go.Figure:
        fig = go.Figure()

        fig.add_trace(
                go.Heatmap(
                    x=df["name_muni"],
                    y=["TOTAL_CASES", "TOTAL_DEATHS"],
                    z=[df["TOTAL_CASES"], df["TOTAL_DEATHS"]],
                    coloraxis="coloraxis",
                    text=df.values,
                    texttemplate="%{text}",
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
            side="top",
            coloraxis=dict(
                colorscale="viridis",
                colorbar=dict(title="Ocorrencias", thickness=15)
            ),
            title=dict(
                text="Top Municipios por Impacto Epidemiologico",
                font=dict(size=18, color="black"),
                x=0.05
            ),
            #title=dict(text="Comparativo de Indicadores por Localidade", font=dict(size=16)),
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(color="black", size=11),
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            yaxis=dict(
                tickfont=dict(color="black", size=12),
                gridcolor="rgba(255,255,255, 0.1)"
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=100, r=50, t=80, b=120)
        )

        return fig
    
    def main(self, disease, year, uf, mun, sex, age, pop):
        df = self.prepare_data(disease=disease, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)
        fig = self.plot(df)
        return fig
    
if __name__ == "__main__":
    load = HeathMap()
    load_main = load.main(disease="CHAG", year=2020, uf="MA", mun=None, sex=None, age=None, pop=None)
    print(load_main)