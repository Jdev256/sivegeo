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
        if len(self.sinan_lf.columns) == 0:
            raise ValueError("O servidor do DATASUS está inacessível no momento (Falha de DNS/Conexão).")
        self.cid_code = self.sinan_lf.select(pl.col("CID").first()).collect().item()
        
        self.sim_lf = self.service.load_data_sim(cid_code=self.cid_code, year=year, uf=uf, mun=mun, sex=sex, age=age, pop=pop)
        self.pop = self.service.load_data_ibge(year=year, uf=uf, mun=mun, pop=pop, source="POP")
        self._geo_keys=["CID","ANO", "UF", "COD_MUN", "name_muni", "POPULACAO"]

    def incidence(self) -> pl.LazyFrame:
        "Incidencia"
        cases = self.indicator.total_cases(self.sinan_lf)
        return cases.with_columns(
            pl.when(pl.col("POPULACAO") > 0)
            .then((pl.col("TOTAL_CASES").cast(pl.Float64) / pl.col("POPULACAO").cast(pl.Float64)) * 100_000)
            .otherwise(0.0)
            .alias("INCIDENCE")
        )

    def mortality(self) -> pl.LazyFrame:
        "Mortalidade"
        deaths = self.indicator.total_deaths(self.sim_lf)

        return deaths.with_columns(
            pl.when(pl.col("POPULACAO") > 0)
            .then((pl.col("TOTAL_DEATHS").cast(pl.Float64) / pl.col("POPULACAO").cast(pl.Float64) * 100_000))
            .otherwise(0.0)
            .alias("MORTALITY")
        )

    def letality(self) -> pl.LazyFrame:
        "Letalidade"
        deaths = self.indicator.total_deaths(self.sim_lf)
        cases = self.indicator.total_cases(self.sinan_lf)

        #(deaths / cases)*100 if cases > 0 else 0

        return (
            cases.join(deaths, on=self._geo_keys, how="full", coalesce=True)
            .with_columns([
                pl.col("TOTAL_CASES").fill_null(0),
                pl.col("TOTAL_DEATHS").fill_null(0)
            ])
            .with_columns(
                pl.when(pl.col("TOTAL_CASES") > 0)
                .then((pl.col("TOTAL_DEATHS").cast(pl.Float64) / pl.col("TOTAL_CASES").cast(pl.Float64)) * 100.0)
                .otherwise(0.0)
                .alias("LETALITY")
            )
        )
    
    def up_week(self) -> pl.LazyFrame:
        "Crescimento"
        return pl.LazyFrame([])
    
    def tendencias(self) -> pl.LazyFrame:
        "Tendencias"
        return pl.LazyFrame([])

    def main(self):
        inc = self.incidence().select(self._geo_keys + ["INCIDENCE"]).filter(pl.col("CID").is_not_null())
        mort = self.mortality().select(self._geo_keys + ["MORTALITY"]).filter(pl.col("CID").is_not_null())
        let = self.letality().select(self._geo_keys + ["TOTAL_CASES", "TOTAL_DEATHS", "LETALITY"]).filter(pl.col("CID").is_not_null())
        kpis_df = (
            let
            .join(inc, on=self._geo_keys, how="full", coalesce=True)
            .join(mort, on=self._geo_keys, how="full", coalesce=True)
            .with_columns([
                pl.col("INCIDENCE").fill_null(0.0),
                pl.col("MORTALITY").fill_null(0.0),
                pl.col("LETALITY").fill_null(0.0)
            ]).sort("ANO", "COD_MUN")
        )
        return kpis_df.collect()

if __name__ == "__main__":
    instance = KPIS(dis_code="CHAG", year=2020, uf="MA", mun=None, age=None, sex=None, pop=None)
    load = instance.main()
    print(load)