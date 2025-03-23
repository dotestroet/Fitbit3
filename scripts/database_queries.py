import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "fitbit_database.db")
MODIFIED_DB_PATH = os.path.join(BASE_DIR, "..", "data", "fitbit_database_modified.db")

def get_table_names(use_modified=False):  
    db_path = MODIFIED_DB_PATH if use_modified else DB_PATH  
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    
    return [table[0] for table in tables]

def get_column_names(table_name, use_modified=False):  
    db_path = MODIFIED_DB_PATH if use_modified else DB_PATH 
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    
    return [col[1] for col in columns]

def fetch_table_data(table_name, use_modified=False):
    db_path = MODIFIED_DB_PATH if use_modified else DB_PATH  
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
    except Exception as e:
        print(f"Error fetching data from {table_name}: {e}")
        return pd.DataFrame() 
    return df

def save_table_data(df, table_name, use_modified=False): 
    db_path = MODIFIED_DB_PATH if use_modified else DB_PATH 
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists='replace', index=False) 
    conn.close()
