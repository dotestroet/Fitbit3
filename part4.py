import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

def load_data(db_path):
    conn = sqlite3.connect(db_path)
    weightlog_data = pd.read_sql_query("SELECT * FROM weight_log", conn)
    conn.close()
    return weightlog_data

def calculate_statistics(weightlog_data):
    median_weight = weightlog_data['WeightKg'].median()
    average_weight = weightlog_data['WeightKg'].mean()
    return median_weight, average_weight

def fill_missing_values(weightlog_data, median_weight):
    weightlog_data['WeightKg'] = weightlog_data['WeightKg'].fillna(median_weight)
    return weightlog_data

def plot_weight_distribution(weightlog_data, median_weight, average_weight):
    plt.figure(figsize=(8, 6))
    weightlog_data['WeightKg'].hist(bins=30, edgecolor='black', color='skyblue', alpha=0.7)
    plt.axvline(average_weight, color='red', linestyle='dashed', linewidth=2, label=f'Average = {average_weight:.2f}')
    plt.axvline(median_weight, color='green', linestyle='dashed', linewidth=2, label=f'Median = {median_weight:.2f}')
    plt.title('Weight Distribution (After Filling Missing Values)')
    plt.xlabel('Weight (kg)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.show()

def detect_outliers(weightlog_data):
    weights = weightlog_data['WeightKg']
    Q1 = weights.quantile(0.25)
    Q3 = weights.quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = weights[(weights < lower_bound) | (weights > upper_bound)]
    num_outliers = outliers.shape[0]
    
    return num_outliers, lower_bound, upper_bound


def choose_statistic(num_outliers):
    if num_outliers > 0:
        return "median (less affected by outliers)"
    else:
        return "mean (reasonable choice)"


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_filename = "fitbit_database.db"
    db_path = os.path.join(script_dir, db_filename)

    weightlog_data = load_data(db_path)
    median_weight, average_weight = calculate_statistics(weightlog_data)
    weightlog_data = fill_missing_values(weightlog_data, median_weight)
    median_weight_filled = weightlog_data['WeightKg'].median()
    average_weight_filled = weightlog_data['WeightKg'].mean()
    plot_weight_distribution(weightlog_data, median_weight_filled, average_weight_filled)
    num_outliers, lower_bound, upper_bound = detect_outliers(weightlog_data)
    
    print(f"Median Weight (kg) after filling NaNs: {median_weight_filled}")
    print(f"Average Weight (kg) after filling NaNs: {average_weight_filled}\n")
    print(f"Number of outliers: {num_outliers}")
    print(f"Outlier bounds: Lower = {lower_bound}, Upper = {upper_bound}")
    print(f"Recommended statistic to use: {choose_statistic(num_outliers)}")

if __name__ == "__main__":
    main()
