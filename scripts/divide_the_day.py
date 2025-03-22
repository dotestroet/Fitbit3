import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_data_from_database(db_path, query): 
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=[x[0] for x in cursor.description])
    connection.close()

    return df

def convert_time_to_twentyfour_hours(df, time_column):
    df['Hour'] = df[time_column].str.split(':').str[0].astype(int)
    df['Hour'] = np.where((df['TimeOfDay'] == 'PM') & (df['Hour'] != 12), df['Hour'] + 12, df['Hour'])
    df['Hour'] = np.where((df['TimeOfDay'] == 'AM') & (df['Hour'] == 12), 0, df['Hour'])
    
    return df

def assign_time_blocks(df):
    time_labels = ['0-4', '4-8', '8-12', '12-16', '16-20', '20-24']
  
    df['TimeBlock'] = pd.cut(df['Hour'], 
                             bins=[0, 4, 8, 12, 16, 20, 24], 
                             labels=time_labels, 
                             right=False, 
                             include_lowest=True)

    return df

def compute_average_per_time_block(df, value_column):
    df_avg = df.groupby('TimeBlock', observed = False).agg({value_column: 'mean'}).reset_index()
    df_avg.rename(columns={value_column: f'Average {value_column}'}, inplace=True)

    return df_avg

def plot_bar_chart(df, value_column, title, ylabel, color):

    plt.figure(figsize=(8, 5))
    plt.bar(df['TimeBlock'], df[value_column], color=color)
    plt.xlabel("Time Block")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45)  
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

def main():
    db_path = os.path.join(BASE_DIR, "..", "data", "fitbit_database_modified.db")

    query_steps_by_pm = "SELECT ActivityHour, StepTotal, TimeOfDay FROM hourly_steps WHERE TimeOfDay = 'PM'"
    query_steps_by_am = "SELECT ActivityHour, StepTotal, TimeOfDay FROM hourly_steps WHERE TimeOfDay = 'AM'"
    query_calories_pm = "SELECT ActivityHour, Calories, TimeOfDay FROM hourly_calories WHERE TimeOfDay = 'PM'"
    query_calories_am = "SELECT ActivityHour, Calories, TimeOfDay FROM hourly_calories WHERE TimeOfDay = 'AM'"
    query_sleep_pm = "SELECT Value AS MinutesAsleep, Time, TimeOfDay FROM minute_sleep WHERE TimeOfDay = 'PM'"
    query_sleep_am = "SELECT Value AS MinutesAsleep, Time, TimeOfDay FROM minute_sleep WHERE TimeOfDay = 'AM'"
 
    steps_pm = load_data_from_database(db_path, query_steps_by_pm)
    steps_am = load_data_from_database(db_path, query_steps_by_am)
    calories_pm = load_data_from_database(db_path, query_calories_pm)
    calories_am = load_data_from_database(db_path, query_calories_am)
    sleep_pm = load_data_from_database(db_path, query_sleep_pm)
    sleep_am = load_data_from_database(db_path, query_sleep_am)

    average_steps = compute_average_per_time_block(assign_time_blocks(convert_time_to_twentyfour_hours(pd.concat([steps_pm, steps_am]), 'ActivityHour')), 'StepTotal')
    average_calories = compute_average_per_time_block(assign_time_blocks(convert_time_to_twentyfour_hours(pd.concat([calories_pm, calories_am]), 'ActivityHour')), 'Calories')

    print("\n Average Steps per Time Block:")
    print(average_steps)

    print("\n Average Calories per Time Block:")
    print(average_calories)

    plot_bar_chart(average_steps, 'Average StepTotal', "Average Steps per 4-Hour Time Block", "Avg Steps", "skyblue")
    plot_bar_chart(average_calories, 'Average Calories', "Average Calories Burnt per 4-Hour Time Block", "Avg Calories", "orange")

if __name__== "__main__":
    main()
