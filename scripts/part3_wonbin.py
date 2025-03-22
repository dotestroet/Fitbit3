# %%
import sqlite3
import pandas as pd
import statsmodels.api as sm
conn = sqlite3.connect("/Users/andrew/Documents/VU_2025_1/Fitbit3/Fitbit3/fitbit_database_modified.db")

# %%
# check each column
# columns_info = {}
# for table_name in tables['name']:
#     query = f"PRAGMA table_info({table_name});"
#     columns_info[table_name] = pd.read_sql_query(query, conn)

# columns_info

# %%
# activity data in daily_activity
activity_query = """
SELECT 
    Id, 
    ActivityDate, 
    VeryActiveMinutes, 
    FairlyActiveMinutes, 
    LightlyActiveMinutes 
FROM 
    daily_activity;
"""

activity_data = pd.read_sql_query(activity_query, conn)

# sleep data in minute_sleep
sleep_query = """
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

sleep_data = pd.read_sql_query(sleep_query, conn)

sleep_data

# %%
# format
activity_data['ActivityDate'] = pd.to_datetime(activity_data['ActivityDate'], format='%m/%d/%Y')
sleep_data['SleepDate'] = pd.to_datetime(sleep_data['SleepDate'], format='%m/%d/%Y %I:%M:%S %p')

# total active time
activity_data['TotalActiveMinutes'] = (
    activity_data['VeryActiveMinutes'] +
    activity_data['FairlyActiveMinutes'] +
    activity_data['LightlyActiveMinutes']
)

activity_data

# %%
# merge activity & sleep data
merged_data = pd.merge(activity_data, sleep_data, left_on=['Id', 'ActivityDate'], right_on=['Id', 'SleepDate'])

# data for regression
X = merged_data['TotalActiveMinutes']
y = merged_data['TotalMinutesAsleep']

# add column of 1
X = sm.add_constant(X)

# model
model = sm.OLS(y, X).fit()

# model results
regression_results = model.summary()
print(regression_results)
