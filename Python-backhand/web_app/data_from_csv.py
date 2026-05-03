import pandas as pd

def extract_data(filename):
    """This function will extract the file data"""
    df = pd.read_excel(f'po_excl/{filename}', usecols=[0,2,3]).dropna()
    return df.drop(df.index[0])