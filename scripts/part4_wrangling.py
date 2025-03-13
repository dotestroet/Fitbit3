import pandas as pd
import shutil
from database_queries import get_table_names, fetch_table_data, save_table_data

DB_PATH = "data/fitbit_database.db"
MODIFIED_DB_PATH = "data/fitbit_database_modified.db"

def check_missing_values(use_modified=False):
    tables = get_table_names()
    missing_values_summary = {}

    for table in tables:
        df = fetch_table_data(table, use_modified=use_modified)
        missing_values = df.isnull().sum()
        missing_values_summary[table] = missing_values[missing_values > 0]
    
    for table, missing_cols in missing_values_summary.items():
        print(f"Missing values in table '{table}':")
        if missing_cols.empty:
            print("  No missing values.")
        else:
            for col, missing_count in missing_cols.items():
                print(f"  - {col}: {missing_count} missing values.")
        print("-" * 50)

def check_duplicates(use_modified=False):
    tables = get_table_names()
    
    for table in tables:
        df = fetch_table_data(table, use_modified=use_modified) 
        duplicates = df[df.duplicated()]
        total_duplicates = len(duplicates)
        
        if total_duplicates > 0:
            total_rows = len(df)
            print(f"Found {total_duplicates}/{total_rows} duplicate rows in table '{table}'.")
        else:
            print(f"No duplicates found in table '{table}'.")

def detect_outliers(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    return outliers

def check_outliers(use_modified=False):
    tables = get_table_names()
    
    for table in tables:
        df = fetch_table_data(table, use_modified=use_modified) 
        for column in df.select_dtypes(include=['float64', 'int64']).columns:
            outliers = detect_outliers(df, column)
            num_outliers = len(outliers)
            total_rows = len(df[column]) 
            
            if num_outliers > 0:
                print(f"Found {num_outliers}/{total_rows} outliers in column '{column}' of table '{table}'.")
            else:
                print(f"No outliers found in column '{column}' of table '{table}'.")

def create_modified_database():
    try:
        shutil.copy(DB_PATH, MODIFIED_DB_PATH)
        print(f"Modified database created: {MODIFIED_DB_PATH}")
    except Exception as e:
        print(f"Error creating modified database: {e}")

def fill_missing_weight(use_modified=False):
    df = fetch_table_data("weight_log", use_modified=use_modified)
    
    if "WeightKg" in df.columns:
        median_weight = df["WeightKg"].median()
        df["WeightKg"].fillna(median_weight, inplace=True)
        
        print(f"Filled missing WeightKg values with median: {median_weight:.2f}")
    save_table_data(df, "weight_log", use_modified=use_modified)
    return df

def remove_fat_column(use_modified=False):
    df = fetch_table_data("weight_log", use_modified=use_modified)
    
    if "Fat" in df.columns:
        df.drop(columns=["Fat"], inplace=True)
        print("Removed 'Fat' column from weight_log table.")

    save_table_data(df, "weight_log", use_modified=use_modified)
    return df

def remove_minute_sleep_outliers(use_modified=False):
    df = fetch_table_data("minute_sleep", use_modified=use_modified)

    if "value" in df.columns:
        outliers = detect_outliers(df, "value")  
        initial_count = len(df)
        df = df[~df.index.isin(outliers.index)] 
        final_count = len(df)
        removed_outliers = initial_count - final_count

        print(f"Removed {removed_outliers} outliers from 'value' column in 'minute_sleep' table.")
        
    save_table_data(df, "minute_sleep", use_modified=use_modified)
    return df

# create_modified_database()
# fill_missing_weight(use_modified=True)
# remove_fat_column(use_modified=True)
# remove_minute_sleep_outliers(use_modified=True)

# check_missing_values(use_modified=True)
# check_duplicates(use_modified=True)
# check_outliers(use_modified=True)
