import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

import statsmodels.api as sm


def load_data(file_path = "dailyactivity.csv"):
    df = pd.read_csv(file_path)
    df["ActivityDate"] = pd.to_datetime(df["ActivityDate"])
    return df

def count_unique_users(df):
    return df["Id"].nunique()

def compute_total_distance(df):
    return df.groupby("Id")["TotalDistance"].sum().reset_index()

def plot_total_distance(user_distance):
    plt.figure(figsize=(12,6))
    sns.barplot(data=user_distance, x ="Id", y = "TotalDistance", hue="Id", legend=False, palette= "viridis")
    plt.xlabel("User ID")
    plt.ylabel("Total Distance")
    plt.title("Total distance per user")
    plt.show()

def plot_calories_burned(df, user_id, start_date = None, end_date = None):
    user_data = df[df["Id"] == user_id]

    if start_date:
        user_data = user_data[user_data["ActivityDate"] >= pd.to_datetime(start_date)]
    if end_date:
        user_data = user_data[user_data["ActivityDate"] <= pd.to_datetime(end_date)]

    plt.figure(figsize = (10,5))
    plt.plot(user_data["ActivityDate"], user_data["Calories"], marker = "o", linestyle = "-", color = "r")
    plt.xlabel("Date")
    plt.ylabel("Calroies burned")
    plt.title(f"Calories Burned by user {user_id}")
    plt.xticks(rotation  = 45)
    plt.grid(True)
    plt.show()


def plot_workout_frequency(df):
    df['DayOfWeek'] = df['ActivityDate'].dt.day_name()
    workout_frequency = df.groupby("DayOfWeek").size().reset_index(name='Frequency')

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    workout_frequency["DayOfWeek"] = pd.Categorical(workout_frequency["DayOfWeek"], categories=day_order, ordered=True)
    workout_frequency = workout_frequency.sort_values("DayOfWeek")


    plt.figure(figsize=(10, 5))
    sns.barplot(data=workout_frequency, x="DayOfWeek", y="Frequency", hue="DayOfWeek", legend=False, palette="Blues_d")
    plt.xlabel("Day of the week")
    plt.ylabel("Frequency of workouts")
    plt.title("Workout frequency by day of the week")
    plt.show()


def linear_regression(df):
    X = df[["TotalSteps", "Id"]]
    X = sm.add_constant(X)
    y = df["Calories"]

    model = sm.OLS(y,X).fit()
    
    print(model.summary())

    return model


def plot_regression_for_user(df, user_id, model):
    user_data = df[df["Id"] == user_id]
    
    X = user_data[["TotalSteps", "Id"]]
    X = sm.add_constant(X)
    y = user_data["Calories"]
    predictions = model.predict(X)

    plt.figure(figsize=(10, 6))
    plt.scatter(user_data["TotalSteps"], y, label="Observed", color="blue")
    plt.plot(user_data["TotalSteps"], predictions, label="Regression Line", color="red")
    plt.xlabel("Total teps")
    plt.ylabel("Calories burned")
    plt.title(f"Linear regresion for user {user_id}")
    plt.legend()
    plt.show()


def main():
    df = load_data("dailyactivity.csv")

    unique_users = count_unique_users(df)
    print(f"Total unique users: {unique_users}")

    user_distance = compute_total_distance(df)
    plot_total_distance(user_distance)

    plot_calories_burned(df, user_id = 1503960366, start_date = "2016-04-12", end_date = "2016-04-20")

    plot_workout_frequency(df)
    model =linear_regression(df)
    plot_regression_for_user(df, user_id = 1503960366, model=model)

if __name__== "__main__":
    main()