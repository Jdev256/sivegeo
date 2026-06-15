import polars as pl
import pandas as pd
from lab.core.data_loader import Pysus


class Indices:
    """Conjunto de Metricas Resumidas """
    def __init__(self):
        self.service = Pysus()

    def epidemic_risk(self):
        "Indice de Risco Epidemiologico "
        "Incidence+Motality+GrowthSpeed+VacineCoberture"
        return df
    
    def severity(self):
        ""
        return df
    
    def vulnerability(self):
        ""
        return df
    
    def heath_esperance(self):
        "sum ages to death / count_deaths"