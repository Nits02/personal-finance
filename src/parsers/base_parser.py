from abc import ABC, abstractmethod
import pandas as pd

class BaseParser(ABC):
    def __init__(self, file_path):
        self.file_path = file_path

    @abstractmethod
    def parse(self) -> pd.DataFrame:
        """
        Parse the file and return a pandas DataFrame.
        """
        pass
