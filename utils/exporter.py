import pandas as pd

def export_csv(df):
    df.to_csv('report.csv', index=False)