import sqlite3
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats


# === DATABASE CONNECTION ===
def connect_to_db(db_path):
    return sqlite3.connect(db_path)

# === SLEEP ANALYSIS ===
def get_asleep_minutes_by_logid(conn):
    query = """
    SELECT logId, COUNT(*) AS asleep_minutes
    FROM minute_sleep
    WHERE value = 1
    GROUP BY logId
    ORDER BY asleep_minutes DESC;
    """
    return pd.read_sql_query(query, conn)

def get_sleep_minutes_per_day(conn):
    query = """
    SELECT Id, Date, COUNT(*) AS asleep_minutes
    FROM minute_sleep
    WHERE value = 1
    GROUP BY Id, Date;
    """
    return pd.read_sql_query(query, conn)

# === ACTIVITY ANALYSIS ===
def get_daily_activity_with_active_minutes(conn):
    df = pd.read_sql_query("SELECT * FROM daily_activity;", conn)
    df["TotalActiveMinutes"] = (
        df["VeryActiveMinutes"] +
        df["FairlyActiveMinutes"] +
        df["LightlyActiveMinutes"]
    )
    return df

# === MERGING & REGRESSION ===
def prepare_merged_data(sleep_df, activity_df):
    sleep_df["Date"] = pd.to_datetime(sleep_df["Date"])
    activity_df["ActivityDate"] = pd.to_datetime(activity_df["ActivityDate"])
    
    merged = pd.merge(
        sleep_df,
        activity_df,
        how="inner",
        left_on=["Id", "Date"],
        right_on=["Id", "ActivityDate"]
    )
    
    # Include SedentaryMinutes in the output
    return merged[[
    "Id", "Date", "asleep_minutes", 
    "VeryActiveMinutes", "FairlyActiveMinutes", "LightlyActiveMinutes", 
    "TotalActiveMinutes", "SedentaryMinutes"
]]


def run_regression(df):
    X = sm.add_constant(df["TotalActiveMinutes"])
    y = df["asleep_minutes"]
    model = sm.OLS(y, X).fit()
    return model

def plot_sleep_vs_activity(df, model):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x="TotalActiveMinutes", y="asleep_minutes", data=df, alpha=0.6)
    
    # Plot regression line
    X_vals = pd.DataFrame({
        "TotalActiveMinutes": sorted(df["TotalActiveMinutes"]),
        "const": 1  # intercept
    })
    y_pred = model.predict(X_vals[["const", "TotalActiveMinutes"]])
    plt.plot(X_vals["TotalActiveMinutes"], y_pred, color='red', label='Regression Line')

    plt.title("Sleep Duration vs Total Active Minutes")
    plt.xlabel("Total Active Minutes")
    plt.ylabel("Minutes Asleep")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def run_sedentary_regression(df):
    X = sm.add_constant(df["SedentaryMinutes"])
    y = df["asleep_minutes"]
    model = sm.OLS(y, X).fit()
    return model

def plot_residual_diagnostics(model):
    residuals = model.resid

    # Histogram
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    sns.histplot(residuals, kde=True, bins=30)
    plt.title("Histogram of Residuals")

    # Q-Q Plot
    plt.subplot(1, 2, 2)
    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title("Q-Q Plot of Residuals")

    plt.tight_layout()
    plt.show()

def plot_sleep_vs_sedentary(df, model):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x="SedentaryMinutes", y="asleep_minutes", data=df, alpha=0.6)

    # Plot regression line
    X_vals = pd.DataFrame({
        "SedentaryMinutes": sorted(df["SedentaryMinutes"]),
        "const": 1  # intercept
    })
    y_pred = model.predict(X_vals[["const", "SedentaryMinutes"]])
    plt.plot(X_vals["SedentaryMinutes"], y_pred, color='red', label='Regression Line')

    plt.title("Sleep Duration vs Sedentary Minutes")
    plt.xlabel("Sedentary Minutes")
    plt.ylabel("Minutes Asleep")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def run_multi_activity_regression(df):
    X = df[["VeryActiveMinutes", "FairlyActiveMinutes", "LightlyActiveMinutes"]]
    X = sm.add_constant(X)
    y = df["asleep_minutes"]
    model = sm.OLS(y, X).fit()
    return model



# === MAIN ===
def main():
    db_path = "data/fitbit_database_modified.db"
    conn = connect_to_db(db_path)

    # Sleep duration per logId
    sleep_by_logid = get_asleep_minutes_by_logid(conn)
    print("Sleep Duration per logId:")
    print(sleep_by_logid.head())

    # --- Merge Daily Sleep and Activity Data ---
    sleep_per_day = get_sleep_minutes_per_day(conn)
    activity_df = get_daily_activity_with_active_minutes(conn)
    merged_df = prepare_merged_data(sleep_per_day, activity_df)
    print("\nMerged Data Preview:")
    print(merged_df.head())

    # --- Regression: Total Active Minutes vs Asleep Minutes ---
    model = run_regression(merged_df)
    print("\nRegression Summary:")
    print(model.summary())

    plot_sleep_vs_activity(merged_df, model)
    
     # --- Regression: Sedentary Minutes vs Asleep Minutes ---
    if "SedentaryMinutes" in activity_df.columns:
        sedentary_model = run_sedentary_regression(merged_df)
        print("\nSedentary Regression Summary:")
        print(sedentary_model.summary())
        plot_residual_diagnostics(sedentary_model)
    
    plot_sleep_vs_sedentary(merged_df, sedentary_model)




if __name__ == "__main__":
    main()
