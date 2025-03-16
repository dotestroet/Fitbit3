import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def plot_heart_rate(user_id, date, nth_exercise):
    """
    Plots the heart rate for a specific user, date, and nth exercise session.

    Parameters:
        user_id (int): The user ID (Id column in database).
        date (str): The date in 'MM/DD/YYYY' format.
        nth_exercise (int): The exercise session number of the day.
    """
    # Define the database path
    db_path = Path(__file__).resolve().parent.parent / "data" / "fitbit_database_modified.db"

    # Connect to the database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Fetch heart rate data for the specific user and date
    query = """
    SELECT Time, TimeOfDay, Value
    FROM heart_rate
    WHERE Id = ? AND Date = ?;
    """
    cursor.execute(query, (user_id, date))
    rows = cursor.fetchall()
    conn.close()

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=['Time', 'TimeOfDay', 'HeartRate'])

    # Combine Time and TimeOfDay, then convert to 24-hour format
    df['Time'] = pd.to_datetime(df['Time'] + " " + df['TimeOfDay'], format='%I:%M:%S %p')

    # Sort by the corrected Time column
    df = df.sort_values(by='Time').reset_index(drop=True)

    # Detect exercise sessions: If a gap of >5 minutes (300 seconds) exists, it's a new session
    df['TimeDiff'] = df['Time'].diff().dt.total_seconds().fillna(0)
    df['Session'] = (df['TimeDiff'] > 300).cumsum() + 1  # Number sessions

    # Get total number of sessions
    total_sessions = df['Session'].nunique()

    # Check if the requested session exists
    if nth_exercise > total_sessions or nth_exercise < 1:
        raise ValueError(f"Invalid session number: {nth_exercise}. Only {total_sessions} sessions available for user {user_id} on {date}.")

    # Select the nth exercise session
    df_exercise = df[df['Session'] == nth_exercise]

    # Plot the heart rate over time
    plt.figure(figsize=(10, 5))
    plt.plot(df_exercise['Time'], df_exercise['HeartRate'], linestyle='-', color='b')

    # Format x-axis as military time (HH:MM)
    plt.xlabel("Time (24-hour format)")
    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%H:%M"))  # Military time

    plt.ylabel("Heart Rate (BPM)")
    plt.title(f"Heart Rate for User {user_id} on {date}, Session {nth_exercise} out of {total_sessions}")
    plt.grid()
    plt.show()

def plot_total_intensity(user_id, date):
    """
    Plots the total intensity for a specific user and date.

    Parameters:
        user_id (int or float): The user ID (Id column in database).
        date (str): The date in 'MM/DD/YYYY' format.
    """
    # Define the database path
    db_path = Path(__file__).resolve().parent.parent / "data" / "fitbit_database_modified.db"

    # Connect to the database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Fetch intensity data for the specific user and date (no sorting in SQL)
    query = """
    SELECT ActivityHour, TimeOfDay, TotalIntensity
    FROM hourly_intensity
    WHERE Id = ? AND Date = ?;
    """
    cursor.execute(query, (user_id, date))
    rows = cursor.fetchall()
    conn.close()

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=['ActivityHour', 'TimeOfDay', 'TotalIntensity'])

    # Combine ActivityHour and TimeOfDay, then convert to 24-hour format
    df['ActivityHour'] = pd.to_datetime(df['ActivityHour'] + " " + df['TimeOfDay'], format='%I:%M:%S %p')

    # Sort by corrected time
    df = df.sort_values(by='ActivityHour').reset_index(drop=True)

    # Plot total intensity over time
    plt.figure(figsize=(10, 5))
    plt.plot(df['ActivityHour'], df['TotalIntensity'], linestyle='-', marker='o', color='r')

    # Format x-axis as military time (HH:MM)
    plt.xlabel("Time (24-hour format)")
    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%H:%M"))

    plt.ylabel("Total Intensity")
    plt.title(f"Total Intensity for User {user_id} on {date}")
    plt.grid()
    plt.show()


plot_heart_rate(2022484408, '4/1/2016', 1)

plot_total_intensity(2022484408, '4/1/2016')
