# Fitbit3
The assignment Fitbit 3 is for the course Data Engineering and is used to create a dashboard

## Exploration
part1_exploration.py 

## Regression
Part3.py

## Data Wrangling
part4_wrangling.py 
Did a small data exploration of fitbit_database.db. Started with data cleaning by finding the outliers, missing, values and duplicates. 
The weight_log table we substituted the missing values with the median, considering the outliers. The fat_column was removed because it missed 31/33 values. Had to remove 525 duplicate rows in table 'minute_sleep'.

## Files Overview

## Key Changes
Renamed files: 
part1.py -> part1_exploration.py
part4.py -> part4_wrangling.py

Added folders:
Created the following folders to organize the project better
    scripts/
    dashboard/
    data/

Added files: database_queries.py. This is the SQL file that part4_wrangling.py uses. 
