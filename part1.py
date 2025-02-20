import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime



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
    sns.barplot(data=user_distance, x ="Id", y = "TotalDistance", palette= "viridis")
    plt.xlabel("User ID")
    plt.ylabel("Total Distance")
    plt.title("Total distance per user")
    plt.show()


def main():
    df = load_data("dailyactivity.csv")

    unique_users = count_unique_users(df)
    print(f"Total unique users: {unique_users}")

    user_distance = compute_total_distance(df)
    plot_total_distance(user_distance)


if __name__== "__main__":
    main()