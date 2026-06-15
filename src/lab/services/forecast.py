from plotly.io import renderers
from prophet import Prophet
import polars as pl
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from lab.core.data_loader import Pysus

class ForecastView:
    def __init__(self):
        self.service = Pysus()
        self.model = None
        self.forecast = None
        self.df_prepared = None

    def load(self, disease, year, uf, mun, sex, age, pop) -> pl.LazyFrame:
        load = self.service.load_data_sinan(dis_code=disease, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)
        return load

    def prepare_data(self, disease, year, uf, mun, sex, age, pop) -> pl.LazyFrame:
        load = self.load(disease=disease, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)
        # 1. convert date
        self.df_prepared = (
            load.filter(pl.col("DT_NOTIFIC").is_not_null())
            .group_by("DT_NOTIFIC")
            .agg(pl.col("TOTAL_CASES").sum().alias("y"))
            .rename({"DT_NOTIFIC":"ds"})
            .sort("ds")
            .collect()
            .to_pandas()
        )
        return self.df_prepared

    def fit(self, periods=30):
        m = Prophet()
        self.model = m
        m.fit(self.df_prepared)

        future = m.make_future_dataframe(periods=periods)

        self.forecast = m.predict(future)
        m.plot_components(self.forecast)
        print(self.forecast[['ds','yhat','yhat_lower','yhat_upper']].tail())
        pass

    def plot(self):
        fig = go.Figure()
        df = self.df_prepared
        forecast = self.forecast

        fig.add_trace(go.Scatter(
            name="Dados Reais",
            mode="markers",
            x=df['ds'],
            y=df['y'],
            marker=dict(color='#3498db',size=5),
            showlegend=True,
        ))
        fig.add_trace(go.Scatter(
            name="Trends",
            mode="lines",
            x=forecast['ds'],
            y=forecast['trend'],
            line=dict(color='yellow', dash='dash', width=1),
            showlegend=True
        ))
        fig.add_trace(go.Scatter(
            name="Forecast",
            mode="lines",
            x=forecast['ds'],
            y=forecast['yhat'],
            line=dict(color='#e74c3c', width=2),
            showlegend=True,
        ))
        fig.add_trace(go.Scatter(
            name="Limite Inferior",
            mode="lines",
            x=forecast['ds'],
            y=forecast['yhat_lower'],
            line=dict(width=0),
            showlegend=True,
            legendgroup='Incerteza',
        ))
        fig.add_trace(go.Scatter(
            name="Incerteza 95%",
            mode="markers+lines",
            x=self.forecast['ds'],
            y=self.forecast['yhat_upper'],
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(203,76,60,0.2)',
            legendgroup='Incerteza',
            showlegend=True,
        ))
        fig.update_layout(
            title=f"Forecast at Trends",
            width=1800,
            height=600,
            xaxis_title="Data",
            yaxis_title="Number of Cases",
            hovermode='x unified'
        )

        return fig
    
    def main(self, d, y, uf, mun, sex, age, pop, p):
        self.prepare_data(disease=d, year=y, uf=uf, mun=mun, pop=pop, sex=sex, age=age)
        self.fit(periods=p)
        return self.plot()

if __name__ == "__main__":
    d_input = input()
    y_input = input()
    uf_input = input()
    instance = ForecastView()
    instance.prepare_data(disease=[d_input], year=[int(y_input)], uf=uf_input, mun=None, age=None, sex=None, pop=None)
    instance.fit(periods=90)
    instance.plot()