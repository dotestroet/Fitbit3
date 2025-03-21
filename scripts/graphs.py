import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def plot_activity_distribution(daily_activity_df):
    activity_sums = daily_activity_df[["VeryActiveMinutes", "FairlyActiveMinutes", 
                                       "LightlyActiveMinutes", "SedentaryMinutes"]].sum()

    # Define color scheme (progressively darker shades of red)
    colors = ["#990000", "#cc3333", "#ff6666", "#ff9999"]

    # Create the pie chart figure
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(activity_sums, labels=activity_sums.index, autopct='%1.1f%%', 
           colors=colors, startangle=140)
    ax.set_title("Distribution of Activity Minutes")

    return fig  

def plot_sleep_duration_histogram(minute_sleep_df):
    """
    Takes a DataFrame of minute_sleep and returns a histogram figure 
    for use in Streamlit.
    """
    # Combine date, time, and TimeOfDay into a single datetime column
    minute_sleep_df["datetime"] = pd.to_datetime(
        minute_sleep_df["Date"] + " " + minute_sleep_df["Time"] + " " + minute_sleep_df["TimeOfDay"], 
        format="%m/%d/%Y %I:%M:%S %p"
    )

    # Calculate sleep duration per logId
    sleep_durations = minute_sleep_df.groupby("logId")["datetime"].agg(["min", "max"])
    sleep_durations["duration"] = (sleep_durations["max"] - sleep_durations["min"]).dt.total_seconds() / 3600  

    # Create the histogram figure
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(sleep_durations["duration"], bins=20, color="skyblue", edgecolor="black", alpha=0.7)
    ax.set_xlabel("Sleep Duration (Hours)")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Sleep Durations")
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    return fig 


def plot_heart_rate(df, user_id, date, nth_exercise):
    """
    Plots the heart rate for a specific user, date, and nth exercise session.

    Parameters:
        df (pd.DataFrame): The heart rate DataFrame containing columns ['Id', 'date', 'time', 'TimeOfDay', 'Value'].
        user_id (int): The user ID.
        date (str): The date in 'MM/DD/YYYY' format.
        nth_exercise (int): The exercise session number of the day.

    Returns:
        fig (matplotlib.figure.Figure): The figure containing the heart rate plot.
    """
    nth_exercise = int(nth_exercise)
    # Filter the DataFrame for the specific user and date
    user_df = df[(df["Id"] == user_id) & (df["Date"] == date)].copy()

    # Combine time columns into a single datetime column
    user_df["Time"] = pd.to_datetime(user_df["Time"] + " " + user_df["TimeOfDay"], format="%I:%M:%S %p")

    # Sort by time
    user_df = user_df.sort_values(by="Time").reset_index(drop=True)

    # Detect exercise sessions: If a gap of >10 minutes (600 seconds) exists, it's a new session
    user_df["TimeDiff"] = user_df["Time"].diff().dt.total_seconds().fillna(0)
    user_df["Session"] = (user_df["TimeDiff"] > 600).cumsum() + 1  # Number sessions

    # Get total number of sessions
    total_sessions = user_df["Session"].nunique()

    # Check if the requested session exists
    if nth_exercise > total_sessions or nth_exercise < 1:
        raise ValueError(f"Invalid session number: {nth_exercise}. Only {total_sessions} sessions available for user {user_id} on {date}.")

    # Select the nth exercise session
    df_exercise = user_df[user_df["Session"] == nth_exercise]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_exercise["Time"], df_exercise["Value"], linestyle="-", color="b")

    # Format x-axis as military time (HH:MM)
    ax.set_xlabel("Time (24-hour format)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.xticks(rotation=45)

    ax.set_ylabel("Heart Rate (BPM)")
    ax.set_title(f"Heart Rate for User {user_id} on {date}, Session {nth_exercise} out of {total_sessions}")
    ax.grid()

    return fig  # Return the figure for use in Streamlit

def plot_total_intensity(df, user_id, date):
    """
    Plots the total intensity for a specific user and date using a DataFrame.

    Parameters:
        df (pd.DataFrame): The DataFrame containing hourly intensity data.
        user_id (int or float): The user ID (Id column in DataFrame).
        date (str): The date in 'MM/DD/YYYY' format.

    Returns:
        fig (matplotlib.figure.Figure): The figure containing the total intensity plot.
    """
    # Filter the DataFrame for the specific user and date
    user_df = df[(df["Id"] == user_id) & (df["Date"] == date)].copy()

    # Combine ActivityHour and TimeOfDay, then convert to 24-hour format
    user_df['ActivityHour'] = pd.to_datetime(
        user_df['ActivityHour'] + " " + user_df['TimeOfDay'], format='%I:%M:%S %p'
    )

    # Sort by corrected time
    user_df = user_df.sort_values(by='ActivityHour').reset_index(drop=True)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(user_df['ActivityHour'], user_df['TotalIntensity'], linestyle='-', marker='o', color='r')

    # Format x-axis as military time (HH:MM)
    ax.set_xlabel("Time (24-hour format)")
    ax.set_xticklabels(user_df['ActivityHour'].dt.strftime('%H:%M'), rotation=45)
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%H:%M"))

    ax.set_ylabel("Total Intensity")
    ax.set_title(f"Total Intensity for User {user_id} on {date}")
    ax.grid(True)

    return fig  # Return the figure for Streamlit usage