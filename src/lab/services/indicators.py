from typing import List
import polars as pl
import pandas as pd
from lab.core.data_loader import Pysus

class Indicators:
    """Medidas"""
    def __init__(self):
        self.load = Pysus()

    def _aggregate(self, lf: pl.LazyFrame, target_col: str) -> pl.LazyFrame:
        keys = ["CID", "ANO", "UF", "COD_MUN", "FAIXA_ETARIA", "SEXO"]

        if target_col in lf.collect_schema().names():
            agg_expr = pl.col(target_col).sum().alias(target_col)
        else:
            agg_expr = pl.len().alias(target_col)

        return (
            lf.group_by(keys)
            .agg([
                agg_expr,
                pl.col("name_muni").first(),
                pl.col("POPULACAO").first(),
            ])
        )
    
    def total_cases(self, df: pl.LazyFrame) -> pl.LazyFrame:
        df = self._aggregate(df, "TOTAL_CASES")
        return df
    
    def total_deaths(self, df: pl.LazyFrame) -> pl.LazyFrame:
        "TOTAL GERAL"
        df = self._aggregate(df, "TOTAL_DEATHS",)
        return df

    def main(self, disease, year, uf, mun, age, sex, pop):
        sinan_lf = self.load.load_data_sinan(
            dis_code=disease, year=year, uf=uf, mun=mun, age=age, sex=sex, pop=pop
        )
        if len(sinan_lf.collect_schema().names()) == 0:
            raise ConnectionError("Falha ao comunicar com o servidor do DATASUS. Tente novamente em instantes.")
        
        cid_code = sinan_lf.select(pl.col("CID").first()).collect().item()
        sim_lf = self.load.load_data_sim(cid_code=cid_code, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)

        keys = ["CID", "ANO", "UF", "COD_MUN", "FAIXA_ETARIA", "SEXO"]
        cases = self.total_cases(sinan_lf)
        deaths = self.total_deaths(sim_lf)
        )

        return  (
            cases.join(deaths, on=keys, how="full", coalesce=True, validate="1:1")
            .with_columns([
                pl.col("TOTAL_CASES").fill_null(0),
                pl.col("TOTAL_DEATHS").fill_null(0)
            ])
            .sort("ANO","COD_MUN")
            .collect()
        )

if __name__ == "__main__":
    load = Indicators()
    loader = load.main(disease="CHAG", year=[2017], uf="MA", mun="Timon", age=None, sex=None, pop=None)
    print(loader)
