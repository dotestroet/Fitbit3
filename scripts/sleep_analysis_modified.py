import os
import sqlite3
import pandas as pd
import statsmodels.api as sm
from datetime import datetime

from database_queries import get_table_names, fetch_table_data, save_table_data


def load_activity_data():
    df = fetch_table_data("daily_activity", use_modified=True)
    df["ActivityDate"] = pd.to_datetime(df["ActivityDate"], format="%m/%d/%Y").dt.date
    df["TotalActiveMinutes"] = (
        df["VeryActiveMinutes"] + df["FairlyActiveMinutes"] + df["LightlyActiveMinutes"]
    )
    return df


def load_sleep_data():
    df = fetch_table_data("minute_sleep", use_modified=True)
    df['SleepDate'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format="%m/%d/%Y %H:%M:%S")
    df = df.groupby(["Id", "logId", "SleepDate"], as_index=False).agg({"value": "sum"})
    df.rename(columns={"value": "TotalMinutesAsleep"}, inplace=True)
    return df

def merge_activity_sleep_data(activity_df, sleep_df):
    sleep_df['SleepDate'] = sleep_df['SleepDate'].dt.date
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
