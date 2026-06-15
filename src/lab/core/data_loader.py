import logging
from typing import List, Union
import polars as pl
import pyarrow.parquet as pq
from polars import LazyFrame
from pysus import SINAN, SIM, SINASC, SIH, PNI
from pysus.online_data import IBGE
from .processor import DataProcessor
import geobr
import numpy as np
import logging
import matplotlib as plt
from pathlib import Path
import os
from abc import ABC

logger = logging.getLogger(__name__)
output_dir = Path('/home/jturingdev/projects/sivegeo/lab/reports/')

class Pysus:
    def __init__(self):
        self.processor = DataProcessor()
        self.uf_map = {
        "AC": 12, "AL": 27, "AM": 13, "AP": 16, "BA": 29, "CE": 23, "DF": 53,
        "ES": 32, "GO": 52, "MA": 21, "MG": 31, "MS": 50, "MT": 51, "PA": 15,
        "PB": 25, "PE": 26, "PI": 22, "PR": 41, "RJ": 33, "RN": 24, "RO": 11,
        "RR": 14, "RS": 43, "SC": 42, "SE": 28, "SP": 35, "TO": 17,
        }
        self._geo_cache = {}

    def _get_municipality_lookup(self, uf: str, year: int) -> pl.LazyFrame:
        years = year[0] if isinstance(year, list) else year
        cache_key = (uf, years)

        if cache_key in self._geo_cache:
            return self._geo_cache[cache_key]
        
        try:
            gdf = geobr.read_municipality(code_muni=uf, year=years)


            gdf_projected = gdf.to_crs(epsg=5880)
            gdf["lon"] = gdf_projected["geometry"].centroid.to_crs(gdf.crs).x
            gdf["lat"] = gdf_projected["geometry"].centroid.to_crs(gdf.crs).y

            gdf_metrico = gdf.to_crs(epsg=31983)
            gdf["raio_km"] = np.sqrt(gdf_metrico["geometry"].area / np.pi) / 1000

            df_lookup = (
                pl.DataFrame(gdf[["code_muni", "name_muni", "lat", "lon", "raio_km"]])
                .lazy()
                .with_columns(
                    pl.col("code_muni")
                    .cast(pl.Utf8)
                    .str.slice(0, 6)
                    .cast(pl.Int32)
                    .alias("COD_MUN")
                )
                .select(["COD_MUN", "name_muni", "lat", "lon", "raio_km"])
            )
            self._geo_cache[cache_key] = df_lookup
            return df_lookup
        except Exception as e:
            return pl.LazyFrame(schema={
                "COD_MUN": pl.Int32, "name_muni": pl.Utf8,
                "lat": pl.Float64, "lon": pl.Float64, "raio_km": pl.Float64
            })
        
    def get_muns(self, uf, year) -> pl.DataFrame:

        return (
            self._get_municipality_lookup(uf, year)
            .select(["COD_MUN", "name_muni"])
            .sort("name_muni")
            .collect()
        )

    def load_data_sim(self, cid_code: Union[str, List[str]], year: Union[int, List[int]], uf: Union[str, List[str]], age: Union[int, List[int]], mun: Union[str, List[str]], sex: Union[int, List[int]], pop: Union[int, List[int]]) -> pl.LazyFrame:
        sim = SIM().load()

        #if isinstance(cid_code, str): '' -> ['']
        #    cid_code = cid_code.split()

        #if isinstance(year, int): 0 -> [0]
        #    years = [year]
        if isinstance(year, list):
            year = list(range(min(year), max(year) +1))

        try:
            files = sim.get_files(group=["CID10"], year=year, uf=uf)
            path = sim.download(files)

            if not path:
                logger.info("Nenhum dado encontrado")
                return pl.LazyFrame()

            if isinstance(path, list):
                df = pl.scan_parquet([str(p) for p in path], extra_columns="ignore")
                logger.info(df.inspect())
            else:
                df = pl.scan_parquet(str(path), extra_columns="ignore")
                logger.info(df.inspect())

            df = df.pipe(self.processor.clean)
            df = df.pipe(self.processor.parse_sim)
            df = df.pipe(self.processor.transform_sim)

            
            uf_code = self.uf_map.get(str(uf))
            if uf is not None:
                if isinstance(uf, str):
                    df = df.filter(pl.col("UF") == int(uf_code))
                elif isinstance(uf, list):
                    df = df.filter(pl.col("UF").is_in(uf_code))
            
            if mun is not None:
                lf_mun = self._get_municipality_lookup(uf, year)
                if isinstance(mun, list):
                    lf_mun = lf_mun.filter(pl.col("name_muni").is_in(mun))
                else:
                    lf_mun = lf_mun.filter(pl.col("name_muni") == mun)

                df = df.join(lf_mun.select("COD_MUN"), on="COD_MUN", how="semi")
                
                #df = df.filter(pl.col("COD_MUN").is_in(lf_mun.select("COD_MUN")))
            
            if year is not None:
                if isinstance(year, int):
                    df = df.filter(pl.col("ANO") == year)
                else:
                    df = df.filter(pl.col("ANO").is_in(year))

            if age is not None and isinstance(age, (tuple, list)) and len(age) == 2:
                df = df.filter(pl.col("IDADE").cast(pl.Int32).is_between(age[0], age[1]))
            elif age is not None:
                df = df.filter(pl.col("IDADE").cast(pl.Int32) == int(age))
                
            if sex is not None:
                df = df.filter(pl.col("SEXO") == sex)

            if cid_code is not None:
                if isinstance(cid_code, str):
                    #df = df.filter(pl.col("CAUSA") == cid_code)
                    df = df.filter(pl.col("CID").str.starts_with(cid_code))
                elif isinstance(cid_code, list):
                    conditions = [pl.col("CID").str.starts_with(c) for c in cid_code]
                    df = df.filter(pl.any_horizontal(conditions))

            print(df.inspect())

            df = df.select(
                pl.col("CID"),
                pl.col("DT_DEATH"),
                pl.col("ANO"),
                pl.col("UF"),
                pl.col("COD_MUN"),
                pl.col("IDADE"),
                pl.col("FAIXA_ETARIA"),
                pl.col("SEXO"),
            )

            df = (df.pipe(self.processor.aggregate_sim))

            ibge_df = self.load_data_ibge(source="POP", year=year, uf=uf, mun=mun, pop=pop)
            df = (df.join(ibge_df, on=["COD_MUN", "ANO"], how="left", coalesce=True))
            return df
        except Exception as e:
            logger.error(f"Erro no load_data_sim: {e}")
            return pl.LazyFrame()

    def load_data_sinan(self, dis_code: Union[str, List[str]], year: Union[int, List[int]], uf: Union[str, List[str]], age: Union[int, List[int]], mun: Union[str, List[str]], sex: Union[int, List[int]], pop: Union[int, List[int]]) -> pl.LazyFrame:
        sinan = SINAN().load()
        
        if isinstance(dis_code, str):
            dis_code = dis_code.split()

        if isinstance(year, int):
            years = [year]
        elif isinstance(year, list):
            years = list(range(min(year), max(year) +1))

        try:
            files = sinan.get_files(dis_code=dis_code, year=years)
            logger.info(files)
            print(f"DEBUG: Arquivos encontrados no servidor para os anos {year}: {files}")
            paths = sinan.download(files)

            if not paths:
                logger.info("Nenhum dado encontrado")
                return pl.LazyFrame()

            if isinstance(paths, list):
                df = pl.scan_parquet([str(p) for p in paths], extra_columns="ignore")
                logger.info(df.inspect())
            else:
                df = pl.scan_parquet(str(paths), extra_columns="ignore")
                logger.info(df.inspect())
            
            df = (
                df
                .pipe(self.processor.clean)
                .pipe(self.processor.parse_sinan)
                .pipe(self.processor.transform_sinan)
            )
            print(type(uf))
            uf_code = self.uf_map.get(str(uf))
            print(uf_code, type(uf_code))

            if uf is not None:
                df = df.filter(pl.col("UF") == int(uf_code))

            if mun is not None:
                lf_mun_filter = self._get_municipality_lookup(uf, year)
                if isinstance(mun, list):
                    lf_mun_filter = lf_mun_filter.filter(pl.col("name_muni").is_in(mun))
                else:
                    lf_mun_filter = lf_mun_filter.filter(pl.col("name_muni") == mun)
                df = df.join(lf_mun_filter.select("COD_MUN"), on="COD_MUN", how="semi")
                #df = df.filter(pl.col("COD_MUN").is_in(lf_mun_filter.select("COD_MUN")))

            if year is not None:
                if isinstance(year, int):
                    df = df.filter(pl.col("ANO") == year)
                elif isinstance(year, list):
                    if len(years) == 1:
                        df = df.filter(pl.col("ANO") == years[0])
                    else:
                        df = df.filter(pl.col("ANO").is_between(years[0], years[-1]))

            if age is not None and isinstance(age, (tuple, list)) and len(age) == 2:
                df = df.filter(pl.col("IDADE").cast(pl.Int32).is_between(age[0], age[1]))
            elif age is not None:
                df = df.filter(pl.col("IDADE").cast(pl.Int32) == int(age))

            if sex is not None:
                df = df.filter(pl.col("SEXO") == sex)

            df = df.select(
                pl.col("CID"),
                pl.col("DT_NOTIFIC"),
                pl.col("ANO"),
                pl.col("UF"),
                pl.col("COD_MUN"),
                pl.col("IDADE"),
                pl.col("FAIXA_ETARIA"),
                pl.col("SEXO")
                )
            
            df = (df.pipe(self.processor.aggregate_sinan))
        
            ibge_df = self.load_data_ibge(source="POP", year=year, uf=uf, mun=mun, pop=pop)
            df = (df.join(ibge_df, on=["COD_MUN", "ANO"], how="left", coalesce=True))
            return df
        except IOError as e:
            logger.error(f"Erro no I/O dos arquivos: {e}")
            return pl.LazyFrame()
        
    #def load_data_sinasc(self, cid_code: Union[str, List[str]], year: Union[int, List[int]], uf: Union[str, List[str]], age: Union[int, List[int]], mun: Union[int, List[int]], sex: Union[int, List[int]], pop: Union[int, List[int]]) -> pl.LazyFrame:
    #    sinasc = SINASC().load()
    #    files = sinasc.get_files(uf=uf, year=year, group=["DN"])
    #    return df
    
    def load_data_ibge(self, source: str, year: Union[int, List[int]], uf: Union[str, List[str]], mun: Union[str, List[str]], pop: Union[int, List[int]]) -> pl.LazyFrame:
        
        if isinstance(source, (list, tuple)):
            source = source[0]
        source = source.strip()

        if isinstance(year, (int, str)):
            year = [int(year)]
        elif isinstance(year, list):
            int_years = [int(y) for y in year]
            year = list(range(min(int_years), max(int_years) + 1))
        else:
            raise TypeError(f" invalid: {type(year)}")

        dfs = []
        if isinstance(year, list):
            for y in year:
                try:
                    raw = IBGE.get_population(source=source, year=y)

                    if isinstance(raw, pl.DataFrame):
                        lf_year =  pl.LazyFrame(raw)
                    elif isinstance(raw, pl.LazyFrame):
                        lf_year = raw
                    else:
                        lf_year = pl.from_pandas(raw).lazy()

                    lf_year = (
                        lf_year
                        .pipe(self.processor.parse_ibge)
                        .pipe(self.processor.transform_ibge)
                    )

                    if year is not None:
                        lf_year = lf_year.filter((pl.col("ANO") == y))

                    uf_code = self.uf_map.get(str(uf))
                    if uf is not None:
                        if isinstance(uf, str):
                            lf_year = lf_year.filter(pl.col("UF") == int(uf_code))
                        elif isinstance(uf, list):
                            lf_year = lf_year.filter(pl.col("UF").is_in(uf_code))
                    if pop is not None:
                        lf_year = lf_year.filter(pl.col("POPULACAO") > int(pop))

                    lookup_df = self._get_municipality_lookup(uf=uf, year=y)
        
                    if isinstance(lookup_df, pl.DataFrame):
                        lookup_df = lookup_df.lazy()
                    
                    lf_year = lf_year.join(lookup_df, on="COD_MUN", how="left")

                    if mun is not None:
                        if isinstance(mun, list):
                            lf_year = lf_year.filter(pl.col("name_muni").is_in(mun))
                        else:
                            lf_year = lf_year.filter(pl.col("name_muni") == mun)

                    dfs.append(lf_year)
                except Exception as e:
                    logger.error(f"Erro no I/O dos arquivos: {e}")
                    raise
            
        if not dfs:
            return pl.LazyFrame()

        df_final = pl.concat(dfs, how="vertical")

        return df_final

    def main(self):
        print("Data loaded successfully")
        load = Pysus()
        while True:
            try:

                try:
                    opc = input("Continuar? y/n: ")
                    if opc.lower() == "n":
                        break
                except Exception as e:
                    e.with_traceback

                year = [2017]
                dis_input = "CHAG"
                uf_input = "MA"
                age = None
                mun = None
                sex = None
                pop=10000

                lf_ibge = load.load_data_ibge(
                    source="POP", 
                    year=year, uf=uf_input, mun=mun, pop=10000)
                
                lf_sinan = load.load_data_sinan(
                    dis_code=dis_input, 
                    year=year, 
                    uf=uf_input, 
                    age=age, 
                    mun=mun, 
                    sex=sex, pop=pop)
                
                cid_code = (lf_sinan.select(pl.col("CID").first()).collect().item())
                print(type(cid_code))
                
                lf_sim = load.load_data_sim(
                    cid_code=cid_code, 
                    year=year, 
                    uf=uf_input, 
                    age=age, 
                    mun=mun, 
                    sex=sex, pop=pop)
                
                self.processor.join_sinan_sim
                
                print("IBGE: \n",lf_ibge.explain(optimized=True))
                print("SIM: \n",lf_sim.explain(optimized=True))
                print("SINAN: \n",lf_sinan.explain(optimized=True))

                ibge = lf_ibge.collect()
                sim = lf_sim.collect()
                sinan = lf_sinan.collect()

                if ibge.height > 0:
                    print("IBGE \n",ibge.head(5))
                if sim.height > 0:
                    print("SIM-COLUMNS: ", sim.columns)
                    print("SIM: \n",sim.head(5))
                    sim.write_excel(f"{output_dir}/relatorio_sim.xlsx")
                if sinan.height > 0:
                    print("SINAN-COLUMNS: ", sinan.columns)
                    print("SINAN: \n",sinan)
                    sinan.write_excel(f"{output_dir}/relatorio_sinan.xlsx")

                if ibge.height == 0:
                    logger.error(f"ERROR IBGE: {ibge.is_empty}")
                if sim.height == 0:
                    logger.error(f"ERROR SIM: {sim.is_empty}")
                if sinan.height == 0:
                    logger.error(f"ERROR SINAN: {sinan.is_empty}")

                #def generate_report(self):
                    #"Relatorio Executivo KPIS graficos rankings"
                    """RELATORIO EPIDEMIOLOGICO"""
                    #ibge_rows = [row[0] for row in ibge.iter_rows()]
                    #sinan_rows = [row[0] for row in sinan.iter_rows()]
                    #cnv=canvas.Canvas(os.path.dirname(__file__+"\\ReportSINAN.pdf"), pagesize=A4)
                    #tabela=Table(sinan.rows())
                    #pdf.build([tabela])
                    #cnv.save()
                    #return pdf.build([tabela])

                print(f"Total de registros populacionais: {lf_ibge.select(pl.len()).collect().item()}")
                
                if mun is not None:
                    count_sinan=lf_sinan.select(pl.len()).collect().item()
                    count_sim=lf_sim.select(pl.len()).collect().item()
                else:
                    count_sinan = lf_sinan.select(pl.len()).collect().item()
                    count_sim = lf_sim.select(pl.len()).collect().item()

                print(f"Total de Casos SINAN: {count_sinan}")
                print(f"Total de Obitos SIM: {count_sim}")
            except Exception as e:
                print(f"\n[FALHA CRITICA NO MAIN]: {e}")

if __name__ == "__main__":
    load = Pysus()
    main = load.main()
    print(main)