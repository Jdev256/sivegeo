import logging
from pandas.core.dtypes.common import is_object_dtype
from polars import Int64, Int32, LazyFrame
import pandas as pd
import polars as pl

class DataProcessor:

    def clean(self, df: LazyFrame) -> LazyFrame:
        df = df.rename({col: col.upper() for col in df.collect_schema().names()})
        #df = df.drop_nans()
        df = df.fill_nan(None)
        return df

    def parse_sinan(self, df: LazyFrame) -> LazyFrame:

        existing_cols = df.collect_schema().names()
        drop_cols = [c for c in ["UF", "ANO"] if c in existing_cols]
        if drop_cols:
            df = df.drop(drop_cols)

        df = df.rename({
            "ID_AGRAVO":"CID",
            "SG_UF_NOT":"UF",
            "NU_ANO":"ANO",
            "ID_MUNICIP":"COD_MUN",
            "CS_SEXO":"SEXO",
            "NU_IDADE_N":"IDADE"
        })
        return( 
            df.with_columns([
                pl.col("CID").str.replace_all(r"\.", "").str.slice(0, 3),
                pl.col("DT_NOTIFIC")
                .cast(pl.Utf8)
                .str.slice(0, 10)
                .str.to_date(format="%Y-%m-%d", strict=False)
                .fill_null(
                    pl.col("DT_NOTIFIC").cast(pl.Utf8).str.to_date(format="%Y%m%d", strict=False)
                ),
                pl.col("IDADE").cast(pl.Utf8, strict=False).str.strip_chars().str.zfill(4),
                pl.col("UF").cast(Int32, strict=False),
                pl.col("ANO").cast(pl.Int32),
                
                pl.col("COD_MUN")
                .cast(pl.Utf8)
                .str.strip_chars()
                .str.extract(r"(\d+)", 1)
                .str.slice(0, 6).cast(pl.Int32, strict=False),              
            ])
        )

    def transform_sinan(self, df: LazyFrame) -> LazyFrame:
        df = df.with_columns(
            pl.when(pl.col("IDADE").str.slice(0, 1) == "1").then(0)
                .when(pl.col("IDADE").str.slice(0, 1) == "2").then(0)
                .when(pl.col("IDADE").str.slice(0, 1) == "3").then(0)
                .when(pl.col("IDADE").str.slice(0, 1) == "4")
                .then(pl.col("IDADE").str.slice(1, 3).cast(pl.Int32))
                .when(pl.col("IDADE").str.slice(0, 1) == "5")
                .then(pl.col("IDADE").str.slice(1, 3).cast(pl.Int32) + 100)
                .otherwise(None).cast(pl.Int32).alias("IDADE")
        )
        df = df.with_columns(
            pl.when(pl.col("IDADE") < 10).then(pl.lit("00-09"))
            .when(pl.col("IDADE") < 20).then(pl.lit("10-19"))
            .when(pl.col("IDADE") < 30).then(pl.lit("20-29"))
            .when(pl.col("IDADE") < 40).then(pl.lit("30-39"))
            .when(pl.col("IDADE") < 50).then(pl.lit("40-49"))
            .when(pl.col("IDADE") < 60).then(pl.lit("50-59"))
            .when(pl.col("IDADE") < 70).then(pl.lit("60-69"))
            .when(pl.col("IDADE") < 80).then(pl.lit("70-79"))
            .otherwise(pl.lit("80+"))
            .alias("FAIXA_ETARIA")
        )
        return df
    
    def aggregate_sinan(self, df: LazyFrame) -> LazyFrame:
        return (
            df.group_by(["CID", "DT_NOTIFIC","ANO", "UF", "COD_MUN", "IDADE", "SEXO"])
            .agg(pl.len().alias("TOTAL_CASES"))
        )
    
    def parse_sim(self, df:LazyFrame) -> LazyFrame:
        df = df.rename({
            "CODMUNRES":"COD_MUN",
            "CAUSABAS":"CID",
            "DTOBITO": "DT_DEATH",
            "HORAOBITO":"TIME"
        })
        return (
            df.with_columns([
                pl.col("COD_MUN")
                .cast(pl.Utf8)
                .str.strip_chars()
                .str.extract(r"(\d+)", 1)
                .str.slice(0, 6)
                .cast(pl.Int32, strict=False),
                
                pl.col("DT_DEATH").str.to_date(format="%d%m%Y", strict=False),

                pl.col("CID")
                .cast(pl.Utf8)
                .str.strip_chars()
                .str.replace_all(r"\.", ""),
                #.str.slice(0, 3),

                #pl.col("IDADE").map_batches(
                #    lambda s: pl.Series(decodifica_idade_SIM(s.to_pandas(), "y")),
                #    return_dtype=pl.Utf8
                #).cast(pl.Int32, strict=False),
                pl.col("IDADE").cast(pl.Utf8, strict=False).str.strip_chars().str.zfill(3),  
                pl.col("SEXO").cast(pl.Utf8).replace({"1":"M","2":"F"}, default=None),
            ])
        )

    def transform_sim(self, df: LazyFrame) -> LazyFrame:
        df = df.with_columns(
            pl.col("DT_DEATH").dt.year().cast(pl.Int32).alias("ANO"),
            pl.col("TIME")
            .str.strip_chars()
            .str.zfill(4)
            .str.to_time(format="%H%M", strict=False),

                pl.when(pl.col("IDADE").str.slice(0, 1) == "1").then(0)
                    .when(pl.col("IDADE").str.slice(0, 1) == "2").then(0)
                    .when(pl.col("IDADE").str.slice(0, 1) == "3").then(0)
                    .when(pl.col("IDADE").str.slice(0, 1) == "4")
                    .then(pl.col("IDADE").str.slice(1, 2).cast(pl.Int32, strict=False))
                    .when(pl.col("IDADE").str.slice(0, 1) == "5")
                    .then(pl.col("IDADE").str.slice(1).cast(pl.Int32, strict=False) + 100)
                    .otherwise(None)
                    .alias("IDADE")
        )
        df = df.with_columns(
                pl.col("COD_MUN").cast(pl.Utf8).str.slice(0, 2)
                .cast(pl.Int32, strict=False)
                .alias("UF")
            )
        df = df.with_columns(
            pl.when(pl.col("IDADE") < 10).then(pl.lit("00-09"))
            .when(pl.col("IDADE") < 20).then(pl.lit("10-19"))
            .when(pl.col("IDADE") < 30).then(pl.lit("20-29"))
            .when(pl.col("IDADE") < 40).then(pl.lit("30-39"))
            .when(pl.col("IDADE") < 50).then(pl.lit("40-49"))
            .when(pl.col("IDADE") < 60).then(pl.lit("50-59"))
            .when(pl.col("IDADE") < 70).then(pl.lit("60-69"))
            .when(pl.col("IDADE") < 80).then(pl.lit("70-79"))
            .otherwise(pl.lit("80+"))
            .alias("FAIXA_ETARIA")
        )
        return df
    
    def aggregate_sim(self, df: LazyFrame) -> LazyFrame:
        return (
            df.group_by(["CID", "DT_DEATH", "ANO", "UF","COD_MUN", "IDADE", "SEXO"])
            .agg(pl.len().alias("TOTAL_DEATHS"))
        )
    
    def parse_ibge(self, df: LazyFrame) -> LazyFrame:
        df = df.rename({"MUNIC_RES":"COD_MUN"})
        df = df.with_columns(pl.col("COD_MUN").str.slice(0, 6).cast(pl.Int32))
        df = df.with_columns(pl.col("ANO").cast(pl.Int32))
        df = df.with_columns(pl.col("POPULACAO")
                             .str.strip_chars()
                             .cast(pl.Int32))
        return df
    
    def transform_ibge(self, df: LazyFrame) -> LazyFrame:
        df = df.with_columns(
                pl.col("COD_MUN").cast(pl.Utf8).str.slice(0, 2)
                .cast(pl.Int32, strict=False)
                .alias("UF")
            )
        return df
    
    def join_sinan_sim(self, df:LazyFrame) -> LazyFrame:
        df = df.join(
            self.aggregate_sim,
            left_on=["CID","DT_NOTIFIC", "ANO", "UF","COD_MUN", "SEXO", "IDADE"],
            right_on=["CID","DT_DEATH", "ANO", "UF","COD_MUN", "SEXO", "IDADE"],
            how="left"
        ).with_columns(
            pl.col("TOTAL_DEATHS").fill_null(0)
        )
        return df