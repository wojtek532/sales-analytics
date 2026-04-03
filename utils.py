import sqlite3
import pandas as pd

DB_PATH = "data/processed/sales.db"

def query(sql: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(sql, conn)