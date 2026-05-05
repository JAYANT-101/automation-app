import pandas as pd

def extract_data(filename):
    """This function will extract the file data"""
    df = pd.read_excel(filename, usecols=[0, 2, 3]).dropna()
    df = df.drop(df.index[0])
    df.columns = ["po_number", "product_name", "target"]
    return df
