from typing import List, Union

import polars as pl
import pandas as pd
from lab.core.data_loader import Pysus
from lab.services.kpis import KPIS
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class HistoricEvolution:
    def __init__(self):
        self.load = Pysus()

    def load_data(self, dis_code, year, uf, mun, age, sex, pop) -> pl.DataFrame:
        kpis = KPIS(dis_code=dis_code, year=year, uf=uf, mun=mun, age=age, sex=sex, pop=pop)
        return kpis.main()
    
    def prepare_data(self, df: pl.DataFrame, metric: Union[str, List[str]]) -> dict:
        
        metrics = [metric] if isinstance(metric, str) else metric
        
        if df.is_empty() or "ANO" not in df.columns or not any(m in df.columns for m in metrics):
            return {m: {"value": 0, "start": 0, "min": 0, "max": 0} for m in metrics}
        
        compiled_stats = {}

        for m in metrics:
            if m not in df.columns:
                compiled_stats[m] = {"value": 0, "start": 0, "min": 0, "max": 0}
                continue
        
            serie = (
                df.group_by("ANO")
                .agg(pl.col(m).mean().alias("METRIC_VALUE"))
                .sort("ANO")
            )
            if serie.is_empty():
                compiled_stats[m] =  {"value": 0, "start": 0, "min": 0, "max": 0, "serie": {}}
                continue
            else:
                compiled_stats[m] = {
                    "value": serie.select(pl.col("METRIC_VALUE").last()).item() if not serie.is_empty() else 0,
                    "start": serie.select(pl.col("METRIC_VALUE").first()).item() if not serie.is_empty() else 0,
                    "min": serie.select(pl.col("METRIC_VALUE").min()).item() if not serie.is_empty() else 0,
                    "max": serie.select(pl.col("METRIC_VALUE").max()).item() if not serie.is_empty() else 0,
                    "serie": serie.to_dict(as_series=False)
            }

        return compiled_stats

    def plot(self, stats: dict, titles: dict = None) -> go.Figure:
        
        fig = go.Figure()
        metrics = list(stats.keys())
        n_metrics = len(metrics)
        titles = titles or {}

        fig = make_subplots(
            rows=1,
            cols=n_metrics,
            specs=[[{"type": "indicator"} for _ in range(n_metrics)]],
            horizontal_spacing=0.08
        )

        layout_annotations = []

        for idx, m in enumerate(metrics):
            col_pos = idx + 1
            st = stats[m]

            v,mn,mx,ref = st["value"], st["min"], st["max"], st["start"]

            print(f"GAUGE DEBUG: Value={v}, Min={mn}, Max={mx}, Range={mx - mn}")

            # amplitude
            r = mx - mn if mx > mn else 1
            title = titles.get(m, m)
        
            # escala de densidade proporcional por quintis
            steps = [
                {"range": [mn + r * 0.00, mn + r * 0.20], "color": "#003049"},
                {"range": [mn + r * 0.20, mn + r * 0.40], "color": "#004d73"},
                {"range": [mn + r * 0.40, mn + r * 0.60], "color": "#0077b6"},
                {"range": [mn + r * 0.60, mn + r * 0.80], "color": "#0096c7"},
                {"range": [mn + r * 0.80, mx], "color": "#00b4d8"},
            ]

            fig.add_trace(
                go.Indicator(
                    mode = "gauge+number+delta",
                    value = v,
                    delta={
                        "reference": ref,
                        "increasing": {"color": "#ff4d4d"},
                        "decreasing": {"color": "#59ff8f"},
                    },
                    number={"font": {"size": 36, "color": "#ffffff"}},
                    title={
                        "text": f"<b>{title}</b>",
                        "font": {"size": 14, "color": "#cccccc"}
                    },
                    domain = {'x':[0,1], 'y':[0,1]},
                    gauge = {
                        "shape": "angular",
                        "axis": {
                            "range": [mn, mx], "tickmode": "auto", "nticks": 5,
                            "tickwidth": 1, "tickcolor": "#1e3d5c",
                            "tickfont": {"color": "#cccccc", "size": 10},
                        },
                        "bgcolor": "rgba(10,10,20,0.5)",
                        "borderwidth": 2, "bordercolor": "gray",
                        "bar": {"color": "#00d4ff", "thickness": 0.20},
                        "steps": steps,
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": v
                        }
                    }
                ),
                row=1, col=col_pos
            )

            col_width = 1.0 / n_metrics
            col_start = idx * col_width
            col_end = col_start + col_width

            padding = 0.02

            layout_annotations.extend([
                dict(
                    x=col_start + padding, 
                    y=0.12, 
                    xref="paper", 
                    yref="paper", 
                    text=f"Min: {mn:.2f}", 
                    showarrow=False, 
                    font=dict(color="#59ff8f", size=10), 
                    align="left"
                ),
                dict(
                    x=col_end - padding, 
                    y=0.12, 
                    xref="paper", 
                    yref="paper", 
                    text=f"Max: {mx:.2f}", 
                    showarrow=False, 
                    font=dict(color="#ff4d4d", size=10), 
                    align="right"
                )
            ])
            
        fig.update_layout(
            width=330 * n_metrics, 
            height=330, 
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor = "rgba(15, 15, 40, 0.7)", 
            plot_bgcolor="rgba(0,0,0,0)",
            template="plotly_dark", 
            font=dict(family="Arial", color="#d0d0ff", size=14),
            annotations=layout_annotations,
            showlegend=False, hovermode=False
        )
        return fig

    def main(self, d, y, uf, mun, sex, age, pop, metric):
        df = self.load_data(dis_code=d, year=y, uf=uf, mun=mun, sex=sex, age=age, pop=pop)
        stats = self.prepare_data(df, metric=metric)
        fig = self.plot(stats)
        return fig

if __name__ == "__main__":
    load = HistoricEvolution()