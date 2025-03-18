import sqlite3
import pandas as pd
import statsmodels.api as sm
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from divide_the_day import convert_time_to_twentyfour_hours, assign_time_blocks

def load_data_from_database(db_path, query): 
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=[x[0] for x in cursor.description])
    connection.close()
    return df

def merge_fitbit_data(hourly_steps_df, hourly_calories_df):
    return pd.merge(hourly_calories_df, hourly_steps_df, on=["Id", "ActivityHour", "Date", "TimeOfDay"], how="inner")

def load_weather_data(file_path):
    weather_df = pd.read_csv(file_path)
    weather_df["datetime"] = pd.to_datetime(weather_df["datetime"])
    weather_df.rename(columns={"datetime": "ActivityHour"}, inplace=True)
    weather_df.drop(columns=["solarradiation", "solarenergy", "uvindex", "severerisk", "icon", "stations", "winddir", "snowdepth", "sealevelpressure", "name", "dew", "windgust"], inplace=True)
    weather_df.fillna({"windgust": 0, "preciptype": "None"}, inplace=True)
    return weather_df

def match_weather_df(weather_df):
    weather_df["ActivityHour"] = pd.to_datetime(weather_df["ActivityHour"])
    weather_df["Date"] = weather_df["ActivityHour"].dt.strftime("%-m/%-d/%Y")
    weather_df["Hour"] = weather_df["ActivityHour"].dt.hour  
    weather_df["MinuteSecond"] = weather_df["ActivityHour"].dt.strftime(":%M:%S")
    weather_df["ActivityHour_12"] = weather_df["Hour"].copy()
    weather_df.loc[weather_df["Hour"] == 0, "ActivityHour_12"] = 12 
    weather_df.loc[weather_df["Hour"] > 12, "ActivityHour_12"] = weather_df["Hour"] - 12  
    weather_df["ActivityHour"] = weather_df["ActivityHour_12"].astype(str) + weather_df["MinuteSecond"]
    weather_df["TimeOfDay"] = "AM"
    weather_df.loc[weather_df["Hour"] >= 12, "TimeOfDay"] = "PM"  
    weather_df.drop(columns=["Hour", "MinuteSecond", "ActivityHour_12"], inplace=True)
    return weather_df

def merge_fitbit_and_weather_data(fitbit_df, weather_df):
    return pd.merge(fitbit_df, weather_df, on=["ActivityHour", "Date", "TimeOfDay"], how="inner")

def run_regression(df, y_variable, x_variables, selected_blocks=None):
    if selected_blocks is not None:
        df = df[df["TimeBlock"].isin(selected_blocks)]
    if df.empty:
        print("No data available for the selected time blocks.")
        return None
    X = df[x_variables]
    y = df[y_variable]  
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    print(f"\nRegression Results for {y_variable}:\n")
    print(model.summary())
    return model

def plot_general_weather_analysis(df, y_variable="StepTotal", x_variable="temp", selected_blocks=None, precip_scale=20):
    if selected_blocks is None:
        selected_blocks = ["8-12", "12-16", "16-20"]
    filtered_df = df[df["TimeBlock"].isin(selected_blocks)]
    filtered_df["Date"] = pd.to_datetime(filtered_df["Date"])
    daily_avg = filtered_df.groupby("Date").agg({
        y_variable: "mean",
        "temp": "mean",
        "precip": "mean"
    }).reset_index()
    daily_avg["precip_scaled"] = daily_avg["precip"] * precip_scale
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.plot(daily_avg["Date"], daily_avg[y_variable], label=f"Avg {y_variable}", color="blue", marker="o", linestyle="-")
    ax1.set_xlabel("Date")
    ax1.set_ylabel(f"Avg {y_variable}", color="blue")
    ax1.tick_params(axis='y', labelcolor="blue")
    ax2 = ax1.twinx()
    ax2.plot(daily_avg["Date"], daily_avg[x_variable], label=f"Avg {x_variable}", color="red", marker="o", linestyle="--")
    if x_variable == "precip":
        ax2.plot(daily_avg["Date"], daily_avg["precip_scaled"], label=f"Avg Precip (x{precip_scale})", color="green", marker="o", linestyle="-.")
    ax2.set_ylabel(f"{x_variable.capitalize()} (scaled for visibility)", color="black")
    plt.title(f"Avg {y_variable} vs. {x_variable} Across All Users (Time Blocks: {', '.join(selected_blocks)})")
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.show()

def plot_user_weather_analysis(df, user_id, y_variable="StepTotal", x_variable="temp", selected_blocks=None, precip_scale=20):
    user_df = df[(df["Id"] == user_id) & (df["TimeBlock"].isin(selected_blocks))]
    if user_df.empty:
        print(f"No data found for user ID {user_id} in time blocks {selected_blocks}.")
        return
    user_df["Date"] = pd.to_datetime(user_df["Date"])
    daily_avg = user_df.groupby("Date").agg({
        y_variable: "mean",
        "temp": "mean",
        "precip": "mean"
    }).reset_index()
    daily_avg["precip_scaled"] = daily_avg["precip"] * precip_scale
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.plot(daily_avg["Date"], daily_avg[y_variable], label=f"Avg {y_variable}", color="blue", marker="o", linestyle="-")
    ax1.set_xlabel("Date")
    ax1.set_ylabel(f"Avg {y_variable}", color="blue")
    ax1.tick_params(axis='y', labelcolor="blue")
    ax2 = ax1.twinx()
    ax2.plot(daily_avg["Date"], daily_avg[x_variable], label=f"Avg {x_variable}", color="red", marker="o", linestyle="--")
    if x_variable == "precip":
        ax2.plot(daily_avg["Date"], daily_avg["precip_scaled"], label=f"Avg Precip (x{precip_scale})", color="green", marker="o", linestyle="-.")
    ax2.set_ylabel(f"{x_variable.capitalize()} (scaled for visibility)", color="black")
    plt.title(f"Avg {y_variable} vs. {x_variable} for User {user_id} (Time Blocks: {', '.join(selected_blocks)})")
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.show()

def main():
    db_path = "/Users/dotestroet/DataEngineering/Fitbit3/data/fitbit_database_modified.db"
    hourly_calories_df = load_data_from_database(db_path, 'SELECT * FROM hourly_calories')
    hourly_steps_df = load_data_from_database(db_path, 'SELECT * FROM hourly_steps')
    weather_df = match_weather_df(load_weather_data('/Users/dotestroet/DataEngineering/Fitbit3/data/Chicago 2016-03-11 to 2016-04-13 hourly.csv'))
    fitbit_df = merge_fitbit_data(hourly_steps_df, hourly_calories_df)
    merged_df = assign_time_blocks(convert_time_to_twentyfour_hours(merge_fitbit_and_weather_data(fitbit_df, weather_df), "ActivityHour"))
    
    selected_blocks = ["8-12", "12-16", "16-20"]
    filtered_df = merged_df[merged_df["TimeBlock"].isin(selected_blocks)]
    filtered_df["temp_squared"] = filtered_df["temp"] ** 2
    
    run_regression(filtered_df, "StepTotal", ["temp", "temp_squared", "precip"], selected_blocks)
    plot_general_weather_analysis(filtered_df, y_variable="StepTotal", x_variable="temp", selected_blocks=selected_blocks)
    plot_user_weather_analysis(filtered_df, user_id=1503960366, y_variable="Calories", x_variable="precip", selected_blocks=selected_blocks)

if __name__ == "__main__":
    main()
