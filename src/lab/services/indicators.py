from typing import List
import polars as pl
import pandas as pd
from lab.core.data_loader import Pysus

class Indicators:
    """Medidas"""
    def __init__(self):
        self.load = Pysus()

    def _aggregate_by_geo_temporal(self, lf: pl.LazyFrame, target_col: str, group_cols: List[str] = ["CID","ANO", "UF","COD_MUN", "name_muni", "POPULACAO"]) -> pl.LazyFrame:
        return (
            lf.group_by(group_cols)
            .agg(pl.col(target_col).sum())
        ) 
    
    def total_cases(self, df: pl.LazyFrame) -> pl.LazyFrame:
        df = self._aggregate_by_geo_temporal(df, "TOTAL_CASES", ["CID","ANO", "UF","COD_MUN", "name_muni", "POPULACAO"])
        return df
    
    def total_deaths(self, df: pl.LazyFrame) -> pl.LazyFrame:
        "TOTAL GERAL"
        df = self._aggregate_by_geo_temporal(df, "TOTAL_DEATHS", ["CID","ANO", "UF","COD_MUN", "name_muni","POPULACAO"])
        return df
    
    def total_nasc(self, df: pl.LazyFrame) -> pl.LazyFrame:
        "TOTAL_NASC"
        return df
    
    def internacoes(self, df: pl.LazyFrame):
        "Taxa de Internacoes"
        return df
    
    def cobertura_vacinal(self, df: pl.LazyFrame):
        "Taxa de Vacinacao"
        return df
    
    def main(self, disease, year, uf, mun, age, sex, pop):
        sinan_lf = self.load.load_data_sinan(
            dis_code=disease, year=year, uf=uf, mun=mun, age=age, sex=sex, pop=pop
        )
        
        cid_code = sinan_lf.select(pl.col("CID").first()).collect().item()
        
        sim_lf = self.load.load_data_sim(cid_code=cid_code, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)

        cases = self.total_cases(sinan_lf)
        deaths = self.total_deaths(sim_lf)
        #ibge_lf = self.load.load_data_ibge(year=year, uf=uf, pop=pop)
        
        indicators_df = (
            cases.join(deaths, on=["CID","ANO", "UF","COD_MUN", "name_muni","POPULACAO"], how="full", coalesce=True)
            .with_columns([
                pl.col("TOTAL_CASES").fill_null(0),
                pl.col("TOTAL_DEATHS").fill_null(0)
            ])
            .sort("ANO","COD_MUN")
        )
        df_final = indicators_df.collect()
        return df_final

    
if __name__ == "__main__":
    load = Indicators()
    loader = load.main(disease="CHAG", year=[2017], uf="MA", mun="Timon", age=None, sex=None, pop=None)
    print(loader)