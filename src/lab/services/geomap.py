import geopandas as gpd
import polars
import geobr
import plotly.graph_objects as go

from src.lab.core.data_loader import Pysus
from src.lab.services.indicators import Indicators

class GeoMap:
    def __init__(self):
        self.load = Pysus()
        self.indicators = Indicators()

    def load(self, df, disease, year, uf, mun, age, sex, pop) -> gpd.GeoDataFrame:
        sinan_lf = self.load.load_data_sinan(
            dis_code=disease, year=year, uf=uf, mun=mun, age=age, sex=sex, pop=pop
        )
        
        cid_code = sinan_lf.select(pl.col("ID_AGRAVO").first()).collect().item()
        
        sim_lf = self.load.load_data_sim(cid_code=cid_code, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)

        total_deaths = Indicators.total_deaths(sim_lf)

        malha = geobr.read_municipality(code_muni=uf, year=year)

        return df
    
    def prepare_data(self, df):
        return df
    
    def plot(self, df):
        return df
    
    def main(self, df):
        return df