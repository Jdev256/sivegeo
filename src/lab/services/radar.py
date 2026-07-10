from typing import List, Union

import polars as pl
import plotly.graph_objects as go

from lab.core.data_loader import Pysus
from lab.services.indicators import Indicators
from lab.services.kpis import KPIS


class Radar:
    def __init__(self):
        self.service = Pysus()
        self.indicators = Indicators()

    def load_data(self, diseases: Union[str, List[str]], year, uf, mun, sex, age, pop) -> pl.DataFrame:
        dis_list = [diseases] if isinstance(diseases, str) else diseases

        dfs = []
        for dis in dis_list:
            try:
                instance = KPIS(dis_code=diseases, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)
                df_dis = instance.main()

                if df_dis.height > 0:
                    df_dis = df_dis.with_columns(pl.lit(dis).alias("AGRAVO")).drop("CID")
                    dfs.append(df_dis)
            except Exception as e:
                print(f"erro {e}")
        
        if not dfs:
            return pl.DataFrame()
        
        return pl.concat(dfs, how="vertical")
    
    def prepare_data(self, df: pl.DataFrame) -> pl.DataFrame:
        if df.height == 0:
            return df
        return (
            df
            .group_by("AGRAVO").agg(
                pl.col("TOTAL_CASES").sum(),
                pl.col("TOTAL_DEATHS").sum(),
                pl.col("POPULACAO").sum(),
            ).with_columns(
                pl.when(pl.col("POPULACAO") > 0)
                .then((pl.col("TOTAL_CASES").cast(pl.Float64) / pl.col("POPULACAO").cast(pl.Float64)) * 100_000)
                .otherwise(0.0)
                .alias("INCIDENCE_RAW"),

                pl.when(pl.col("POPULACAO") > 0)
                .then((pl.col("TOTAL_DEATHS").cast(pl.Float64) / pl.col("POPULACAO").cast(pl.Float64) * 100_000))
                .otherwise(0.0)
                .alias("MORTALITY_RAW"),

                pl.when(pl.col("TOTAL_CASES") > 0)
                .then((pl.col("TOTAL_DEATHS").cast(pl.Float64) / pl.col("TOTAL_CASES").cast(pl.Float64)) * 100.0)
                .otherwise(0.0)
                .alias("LETALITY_RAW") 
            ).with_columns(
                (pl.col("INCIDENCE_RAW") / pl.col("INCIDENCE_RAW").max()).alias("INCIDENCE"),
                (pl.col("MORTALITY_RAW") / pl.col("MORTALITY_RAW").max()).alias("MORTALITY"),
                (pl.col("LETALITY_RAW") / pl.col("LETALITY_RAW").max()).alias("LETALITY")
            )
            .unpivot(
                on=["INCIDENCE", "MORTALITY", "LETALITY"],
                index=["AGRAVO"],
                variable_name="INDICADOR",
                value_name="VALUE")
        )
        

    def plot(self, df: pl.DataFrame) -> go.Figure:

        fig = go.Figure()

        if df.height == 0:
            fig.update_layout(title="Nenhum dado")
            return fig
        
        diseases = df["AGRAVO"].unique().to_list()

        label_map = {
            "INCIDENCE_RAW": "<b>Incidência</b>",
            "LETALITY": "<b>Letalidade</b>",
            "MORTALITY": "<b>Mortalidade</b>"
        }

        for dis in diseases:
            df_disease = df.filter(pl.col("AGRAVO")==dis)
            
            r = df_disease["VALUE"].to_list()
            theta_list = [label_map.get(t, t) for t in df_disease["INDICADOR"].to_list()]

            if r and theta_list:
                r.append(r[0])
                theta_list.append(theta_list[0])
            
                fig.add_trace(
                    go.Scatterpolar(
                        r=r,
                        theta=theta_list,
                        fill="toself",
                        name=dis,
                        opacity=0.8
                    )
                )

        fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    ),
                    bgcolor="rgba(0,0,0,0)",
                    angularaxis=dict(
                        showticklabels=True,
                        tickfont=dict(
                        family="Arial, sans-serif",
                        size=14,
                        color="white",
                        weight="bold"
                        ),
                        gridcolor="gray",
                        linecolor="white"
                    ),
                ),
                showlegend=True,
                height=650,
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=40, r=40, t=40, b=40)
            )
        return fig
    
    def main(self, dis: Union[str, List[str]], year, uf, mun, sex, age, pop):
        df = self.load_data(diseases=dis, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)
        df_kpis = self.prepare_data(df)
        fig = self.plot(df=df_kpis)
        return fig