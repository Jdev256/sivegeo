
from abc import ABC


class Loader(ABC):
    def __init__(self):
        super().__init__()

    def get_files(self, df):
        return df
    
    def pipe(self, df):
        return df

    def filter(self, df):
        return df    
    
    def select(self, df):
        return df
    
    def aggregate(self, df):
        return df
    
    def join(self, df):
        return df
    
    def export(self, df):
        return df

class SimLoader(Loader):
    def __init__(self):
        super().__init__()
        
class SinanLoader(Loader):
    def __init__(self):
        super().__init__()

class IbgeLoader(Loader):
    def __init__(self):
        super().__init__()

class SihLoader(Loader):
    def __init__(self):
        super().__init__()