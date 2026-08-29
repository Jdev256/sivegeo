import polars as pl
import pandas as pd
from lab.core.data_loader import Pysus
from lab.services.indicators import Indicators

class KPIS:
    def __init__(self, dis_code, year, uf, mun, age, sex, pop):
        self.service = Pysus()
        self.indicator = Indicators()
        
        self.sinan_lf = self.service.load_data_sinan(
            dis_code=dis_code, year=year, uf=uf, mun=mun, age=age, sex=sex, pop=pop
        )
        if len(self.sinan_lf.collect_schema().names()) == 0:
            raise ValueError("O servidor do DATASUS está inacessível no momento (Falha de DNS/Conexão).")
        
        self.cid_code = self.sinan_lf.select(pl.col("CID").first()).collect().item()
        
        self.sim_lf = self.service.load_data_sim(cid_code=self.cid_code, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)
        self.pop = self.service.load_data_ibge(year=year, uf=uf, mun=mun, pop=pop, source="POP")
        self._geo_keys=["CID","ANO", "UF", "COD_MUN", "name_muni", "POPULACAO","FAIXA_ETARIA", "SEXO"]


    def main(self):
        deaths = self.indicator.total_deaths(self.sim_lf)
        cases = self.indicator.total_cases(self.sinan_lf)

        kpis_lf = (
            cases.join(deaths, on=self._geo_keys, how="full", coalesce=True, validate="1:1")
            .with_columns([
                pl.col("TOTAL_CASES").fill_null(0),
                pl.col("TOTAL_DEATHS").fill_null(0)
            ])
        )

        kpis_lf = kpis_lf.with_columns([
            # Letalidade: (Óbitos / Casos) * 100
            pl.when(pl.col("TOTAL_CASES") > 0)
            .then((pl.col("TOTAL_DEATHS").cast(pl.Float64) / pl.col("TOTAL_CASES").cast(pl.Float64)) * 100.0)
            .otherwise(0.0)
            .alias("LETALITY"),

            # Incidência: (Casos / População) * 100.000
            pl.when(pl.col("POPULACAO") > 0)
            .then((pl.col("TOTAL_CASES").cast(pl.Float64) / pl.col("POPULACAO").cast(pl.Float64)) * 100_000.0)
            .otherwise(0.0)
            .alias("INCIDENCE"),

            # Mortalidade: (Óbitos / População) * 100.000
            pl.when(pl.col("POPULACAO") > 0)
            .then((pl.col("TOTAL_DEATHS").cast(pl.Float64) / pl.col("POPULACAO").cast(pl.Float64)) * 100_000.0)
            .otherwise(0.0)
            .alias("MORTALITY")
        ])

        return (
            kpis_lf
            .filter(pl.col("CID").is_not_null())
            .sort("ANO", "COD_MUN")
            .collect()
        )

if __name__ == "__main__":
    instance = KPIS(dis_code="ACBI", year=2025, uf="MA", mun=None, age=None, sex=None, pop=None)
    load = instance.main()
    print(load)