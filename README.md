# Fitbit3
The assignment Fitbit 3 is for the course Data Engineering and is used to create a dashboard for visualizing ana anlyzing Fitbit Data.

## Overview
This project involves the following major tasks:
Exploration of the fitbit data to understand its structure
Data Wrangling where data cleanring, feature engineering, and mergings datasets are done to prepare the data for analysis and visualizion in the dashboard. 
Dashboard development for interactive data visualization

## File Overview

## Exploration
part1_exploration.py 

## weather analysis
This part is an interactive dashboard that analyzes the relationship between weather variables and activity metrics.
### features
- General regression analysis: Understand the overall impact of selected weahter variables on activity metrics.
- User-specific:  Perform personalized regression analysis for individual users.
- Time Block Selection: Analyze specific time periods to capture changes throughout the day.
- Weather variables: Choose from temperature, temperature squared and precipitation as predictors.
- Interactive Plots: Visualize reression results and data trends.
### How to Use
- Select User Id and Time Blocks: Choose the user and specific time ranges from the sidebar.
- Choose Target and Weather Variables: pick the activity metric to analyzse and weather variables to include.
- the Dasboard will display: Regression results and grapic analysis


## Data Wrangling (part4_wrangling.py)
Did a small data exploration of fitbit_database.db. Started with data cleaning by finding the outliers, missing, values and duplicates. 
The weight_log table we substituted the missing values with the median, considering the outliers. The fat_column was removed because it missed 31/33 values. Had to remove 525 duplicate rows in table 'minute_sleep'.

Duplicate removed for table minute_sleep
Ranamed a column from 'date' to 'Date'
Merged data from multiple tables:
    Hourly Activity Data: Steps, calories, and intensity are now combined into a unified dataset.
    Sleep Activity Data: The 'minute_sleep' table is merged with activity data for enriched insights.
    Heart Rate Activity Data: Heart rate data is merged with daily activity data for comprehensive tracking.

Implemented checks to ensure there are no missing values, duplicates or other issues. 

## Changed Sleep_Analysis_modified
This file does the Regression for sleep Anaysis. 

## Dashboard
dashboard/app.py - Streamlit is used
Features
- User activity analysis
- time based trends
sleep analysis
weather impact on activity
database management tools

## Folder Structure 

scripts: 
dashboard:
data:

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
