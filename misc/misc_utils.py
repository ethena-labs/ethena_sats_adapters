import pandas as pd


def load_csv(filename: str) -> pd.DataFrame:
    return pd.read_csv(filename)
