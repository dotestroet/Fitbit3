import os
import sqlite3
import pandas as pd
import statsmodels.api as sm
from datetime import datetime

DB_PATH = "data/fitbit_database_modified.db"

def load_data_from_database(db_path, query):
    connection = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df

def load_activity_data():
    query = """
    SELECT 
        Id, 
        ActivityDate, 
        VeryActiveMinutes, 
        FairlyActiveMinutes, 
        LightlyActiveMinutes 
    FROM 
        daily_activity;
    """
    df = load_data_from_database(DB_PATH, query)
    df["ActivityDate"] = pd.to_datetime(df["ActivityDate"], format="%m/%d/%Y")
    df["TotalActiveMinutes"] = (
        df["VeryActiveMinutes"] + df["FairlyActiveMinutes"] + df["LightlyActiveMinutes"]
    )
    return df

def load_sleep_data():
    query = """
    SELECT 
        Id, 
        date as SleepDate, 
        logId, 
        SUM(value) as TotalMinutesAsleep 
    FROM 
        minute_sleep 
    GROUP BY 
        Id, logId, SleepDate;
    """
    df = load_data_from_database(DB_PATH, query)
    df["SleepDate"] = pd.to_datetime(df["SleepDate"], format="%m/%d/%Y")

    return df

def merge_activity_sleep_data(activity_df, sleep_df):
    merged_df = pd.merge(activity_df, sleep_df, left_on=["Id", "ActivityDate"], right_on=["Id", "SleepDate"])
    return merged_df

def run_regression(df):
    X = sm.add_constant(df["TotalActiveMinutes"])
    y = df["TotalMinutesAsleep"]
    model = sm.OLS(y, X).fit()
    print("\nRegression Results:\n")
    print(model.summary())
    return model

if __name__ == "__main__":
    activity_df = load_activity_data()
    sleep_df = load_sleep_data()
    merged_df = merge_activity_sleep_data(activity_df, sleep_df)
    run_regression(merged_df)
