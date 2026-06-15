import polars as pl
from lab.core.data_loader import Pysus

class Distribution:
    def __init__(self):
        self.load = Pysus()

    def distribution_per_age(self):

        load_sinan = self.load.load_data_sinan(dis_code=disease, year=year, uf=uf, age=age).collect()

        df = (load_sinan
            .with_columns(
                pl.col("NU_IDADE_N")
                .cast(pl.Utf8)
                .str.slice(2,3)
                .cast(Int32, strict=False)
                .alias("AGE")
                )
            )
        return df
    

def prepare_data(disease, year, uf, age):
    
    return df

def plat():
    return df

def main(d,y,u,age):
    df = prepare_data(disease=d, year=y, uf=u, age=age)
    print(df)
    return df

if __name__ == "__main__":
    d=input()
    y=input()
    u=input()
    age=input()
    main(d=d,y=y,u=u,age=age)