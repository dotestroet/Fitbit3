import pandas as pd
import shutil
import matplotlib.pyplot as plt
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


def remove_minute_sleep_duplicates(use_modified=False):
    df = fetch_table_data("minute_sleep", use_modified=use_modified)

    if "value" in df.columns:
        initial_count = len(df)
        df = df.drop_duplicates()
        final_count = len(df)
        removed_duplicates = initial_count - final_count

        print(f"Removed {removed_duplicates} duplicate rows from 'minute_sleep' table.")

    save_table_data(df, "minute_sleep", use_modified=use_modified)
    return df


def rename_date_column(table_name):
    df = fetch_table_data(table_name)
    if 'date' in df.columns:
        df.rename(columns={'date': 'Date'}, inplace=True)
        save_table_data(df, table_name)

        print(f"Renamed 'date' column to 'Date' in table: {table_name}")
    else:
        print(f"No 'date' column found in table: {table_name}")


def split_time_column(table_name, time_column_name):
    df = fetch_table_data(table_name)

    if time_column_name not in df.columns:
        print(f"Column '{time_column_name}' not found in table '{table_name}'")
        return

    if time_column_name == 'Date':
        df[['Date', 'Time', 'TimeOfDay']] = df[time_column_name].str.extract(r'(\d{1,2}/\d{1,2}/\d{4})\s(\d{1,2}:\d{2}:\d{2})\s(AM|PM)')
    else:
        df[['Date', 'ExtractedTime', 'TimeOfDay']] = df[time_column_name].str.extract(r'(\d{1,2}/\d{1,2}/\d{4})\s(\d{1,2}:\d{2}:\d{2})\s(AM|PM)')

        df[time_column_name] = df['ExtractedTime']
        df.drop(['ExtractedTime'], axis=1, inplace=True)

    print(f"Processed table: {table_name}")
    print(df.head())

    save_table_data(df, table_name, use_modified=True)
    print(f"Table '{table_name}' has been saved to the modified database.")



def merge_hourly_activity_data(use_modified=False):
    steps_df = fetch_table_data("hourly_steps", use_modified=use_modified)
    calories_df = fetch_table_data("hourly_calories", use_modified=use_modified)
    intensity_df = fetch_table_data("hourly_intensity", use_modified=use_modified)

    steps_df = steps_df.drop_duplicates(subset=["Id", "ActivityHour", "Date"])
    calories_df = calories_df.drop_duplicates(subset=["Id", "ActivityHour", "Date"])
    intensity_df = intensity_df.drop_duplicates(subset=["Id", "ActivityHour", "Date"])

    merged_df = steps_df.merge(calories_df, on=["Id", "ActivityHour", "Date"], how="inner")
    merged_df = merged_df.merge(intensity_df, on=["Id", "ActivityHour", "Date"], how="inner")
    merged_df = merged_df.drop_duplicates()

    save_table_data(merged_df, "merged_hourly_activity", use_modified=use_modified)
    return merged_df


def merge_sleep_activity_data(use_modified=False):
    sleep_df = fetch_table_data("minute_sleep", use_modified=use_modified)
    activity_df = fetch_table_data("daily_activity", use_modified=use_modified)

    if 'ActivityDate' in activity_df.columns:
        activity_df.rename(columns={'ActivityDate': 'Date'}, inplace=True)

    sleep_df = sleep_df.drop_duplicates(subset=["Id", "Date"])
    activity_df = activity_df.drop_duplicates(subset=["Id", "Date"])

    merged_df = sleep_df.merge(activity_df, on=["Id", "Date"], how="inner")
    merged_df = merged_df.drop_duplicates()

    save_table_data(merged_df, "merged_sleep_activity", use_modified=use_modified)
    return merged_df



def merge_heart_rate_activity_data(use_modified=False):
    heart_rate_df = fetch_table_data("heart_rate", use_modified=use_modified)
    activity_df = fetch_table_data("daily_activity", use_modified=use_modified)

    if 'ActivityDate' in activity_df.columns:
        activity_df.rename(columns={'ActivityDate': 'Date'}, inplace=True)

    heart_rate_df = heart_rate_df.drop_duplicates(subset=["Id", "Date"])
    activity_df = activity_df.drop_duplicates(subset=["Id", "Date"])

    merged_df = heart_rate_df.merge(activity_df, on=["Id", "Date"], how="inner")

    merged_df = merged_df.drop_duplicates()
    
    save_table_data(merged_df, "merged_heart_rate_activity", use_modified=use_modified)
    return merged_df


def check_merged_data(merge_function, data_label, use_modified=False):
    print(f"\nChecking {data_label}...")

    merged_df = merge_function(use_modified=use_modified)
    merged_df = merged_df.drop_duplicates()
    total_rows, total_columns = merged_df.shape
    print(f"Total Rows: {total_rows}, Total Columns: {total_columns}")

    missing_values = merged_df.isnull().sum()
    print("\nMissing Values:")
    print(missing_values[missing_values > 0] if missing_values.any() else "No missing values found.")

    duplicate_count = merged_df.duplicated().sum()
    print(f"\nTotal Duplicate Rows: {duplicate_count}")

    print("\nData Types:")
    print(merged_df.dtypes)

    return merged_df


create_modified_database()
fill_missing_weight(use_modified=True)
remove_fat_column(use_modified=True)
remove_minute_sleep_duplicates(use_modified=True)
rename_date_column("minute_sleep")

split_time_column("heart_rate", "Time")  
split_time_column("hourly_calories", "ActivityHour")  
split_time_column("hourly_intensity", "ActivityHour")  
split_time_column("hourly_steps", "ActivityHour")  
split_time_column("minute_sleep", "Date")  
split_time_column("weight_log", "Date")  

check_missing_values(use_modified=True)
check_duplicates(use_modified=True)
check_outliers(use_modified=True)

merge_hourly_activity_data(use_modified=True)
merge_sleep_activity_data(use_modified=True)
merge_heart_rate_activity_data(use_modified=True)

check_merged_data(merge_hourly_activity_data, "Hourly Activity Data", use_modified=True)
check_merged_data(merge_sleep_activity_data, "Sleep Activity Data", use_modified=True)
check_merged_data(merge_heart_rate_activity_data, "Heart Rate Activity Data", use_modified=True)


