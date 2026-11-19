import pandas as pd


def read_data() -> pd.DataFrame:
    """
    Read the data from the Excel file and return it as a pandas DataFrame.
    """
    df = pd.read_excel("data.csv")
    
    return df


def fill_grids(grids: list[list[list[bool]]], max_candidates: int = 10, max_attempts: int = 10_000) -> list[list[list[bool]]]:
    """
    Fill the provided grids with definitions according to the constraints.
    """

