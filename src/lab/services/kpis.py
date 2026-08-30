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
        self._geo_keys = ["CID", "ANO", "UF", "COD_MUN", "FAIXA_ETARIA", "SEXO"]

    @staticmethod
    def _merge_case_death_data(cases: pl.DataFrame, deaths: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
        if cases.is_empty() and deaths.is_empty():
            return pl.DataFrame(schema={"CID": pl.String, "ANO": pl.Int32, "UF": pl.Int32, "COD_MUN": pl.Int32, "FAIXA_ETARIA": pl.String, "SEXO": pl.String})

        cases_unique = cases.group_by(keys).agg([
            pl.col("TOTAL_CASES").sum().alias("TOTAL_CASES"),
            pl.col("name_muni").first().alias("name_muni"),
            pl.col("POPULACAO").first().alias("POPULACAO"),
        ])
        deaths_unique = deaths.group_by(keys).agg([
            pl.col("TOTAL_DEATHS").sum().alias("TOTAL_DEATHS"),
            pl.col("name_muni").first().alias("name_muni"),
            pl.col("POPULACAO").first().alias("POPULACAO"),
        ])

        return (
            cases_unique
            .join(deaths_unique, on=keys, how="full", coalesce=True)
            .with_columns([
                pl.col("TOTAL_CASES").fill_null(0),
                pl.col("TOTAL_DEATHS").fill_null(0),
                pl.col("POPULACAO").fill_null(0),
            ])
        )

    def main(self):
        deaths = self.indicator.total_deaths(self.sim_lf).collect()
        cases = self.indicator.total_cases(self.sinan_lf).collect()

        kpis_df = self._merge_case_death_data(cases, deaths, self._geo_keys)

        kpis_df = kpis_df.with_columns([
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
            kpis_df
            .filter(pl.col("CID").is_not_null())
            .sort("ANO", "COD_MUN")
        )

if __name__ == "__main__":
    instance = KPIS(dis_code="ACBI", year=2025, uf="MA", mun=None, age=None, sex=None, pop=None)
    load = instance.main()
    print(load)
