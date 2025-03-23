import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import statsmodels.api as sm
import scipy.stats as stats
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from scripts.database_queries import fetch_table_data, get_table_names, save_table_data
from scripts.graphs import *
from scripts.weather_analysis import merged_df, run_weather_regression_, plot_general_weather_analysis, plot_user_weather_analysis
from scripts.divide_the_day import convert_time_to_twentyfour_hours, assign_time_blocks
from scripts.new_sleep_analysis import (
    connect_to_db,
    get_sleep_minutes_per_day,
    get_daily_activity_with_active_minutes,
    prepare_merged_data,
    run_regression,
    plot_sleep_vs_activity,
    run_sedentary_regression,
    plot_sleep_vs_sedentary,
    plot_residual_diagnostics
)

st.set_page_config(layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📊 User Statistics", "⏳ Time-based Analysis", "💤 Sleep Analysis", "🌦️ Weather & Activity", "🔧 Database Management"])

# Go to the folder where app.py is and then command: streamlit run app.py

# =================== Home Page ===================
if page == "🏠 Home":
    st.title("Fitbit Research Dashboard")
    st.write("This dashboard presents an analysis of Fitbit users' activity, sleep, and other fitness metrics.")
    
    daily_activity = fetch_table_data("daily_activity", use_modified=True)
    sleep_data = fetch_table_data("merged_sleep_activity", use_modified=True)  
    
    if 'TotalActiveMinutes' not in daily_activity.columns:
        daily_activity['TotalActiveMinutes'] = (
            daily_activity['VeryActiveMinutes'] + 
            daily_activity['FairlyActiveMinutes'] + 
            daily_activity['LightlyActiveMinutes']
        )
    

    total_users = daily_activity["Id"].nunique()
    
    avg_steps = daily_activity["TotalSteps"].mean()
    avg_calories = daily_activity["Calories"].mean()
    avg_active_minutes = daily_activity["TotalActiveMinutes"].mean()
    
    total_calories = daily_activity["Calories"].sum()
    total_active_minutes = daily_activity["TotalActiveMinutes"].sum()

    total_days = len(daily_activity["ActivityDate"].unique())
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Users", total_users)
    with col2:
        st.metric("Total Number of Days Recorded", total_days)
    with col3:
        st.metric("Average Steps Per Day", round(avg_steps, 2))
    with col4:
        st.metric("Average Calories Burnt Per Day", round(avg_calories, 2))
    with col5:
        st.metric("Average Active Minutes Per Day", round(avg_active_minutes, 2))

    col6, col7 = st.columns(2)

    with col6:
        st.pyplot(plot_activity_distribution(daily_activity))
    with col7:
        st.pyplot(plot_sleep_duration_histogram(fetch_table_data("minute_sleep", use_modified=True)))


# =================== Database Management ===================
elif page == "🔧 Database Management":
    st.title("Database Management")
    
    tables = get_table_names(use_modified=True)
    st.subheader("Tables in Database")
    st.write(tables)

    table_name = st.selectbox("Select Table", tables)
    table_data = fetch_table_data(table_name, use_modified=True) 
    
    st.subheader(f"Data from {table_name}")
    st.dataframe(table_data)
    
    st.info("Data modification is disabled. You can view data but cannot edit or save changes.")

# =================== User Statistics ===================

elif page == "📊 User Statistics":
    st.title("User Activity Analysis")
    
    daily_activity = fetch_table_data("daily_activity", use_modified=True)  
    sleep_data = fetch_table_data("merged_sleep_activity", use_modified=True)  
    heart_rate_data = fetch_table_data("heart_rate", use_modified=True)
    weight_data = fetch_table_data("weight_log", use_modified=True)

    user_id = st.sidebar.selectbox("Select User ID", daily_activity["Id"].unique())

    user_data = daily_activity[daily_activity["Id"] == user_id]
    user_sleep_data = sleep_data[sleep_data["Id"] == user_id]
    user_heart_rate_data = heart_rate_data[heart_rate_data["Id"] == user_id]
    user_weight_data = weight_data[weight_data["Id"] == user_id]

    total_steps = user_data["TotalSteps"].sum()
    total_calories = user_data["Calories"].sum()
    avg_steps = user_data["TotalSteps"].mean()
    avg_calories = user_data["Calories"].mean()

    #avg_resting_heart_rate = user_heart_rate_data["RestingHeartRate"].mean() if not user_heart_rate_data.empty else 0
    avg_weight = user_weight_data["WeightKg"].mean() if not user_weight_data.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Steps", round(total_steps, 2))
    with col2:
        st.metric("Total Calories Burnt", round(total_calories, 2))
    with col3:
        st.metric("Average Steps Per Day", round(avg_steps, 2))
    with col4:
        st.metric("Average Calories Burnt Per Day", round(avg_calories, 2))

    #if avg_resting_heart_rate > 0:
    #    st.metric("Average Resting Heart Rate", round(avg_resting_heart_rate, 2))
    
    if avg_weight > 0:
        with col5:
            st.metric("Average Weight (kg)", round(avg_weight, 2))

    col6, col7 = st.columns(2)
    st.subheader(f"Calories Burnt Over Time for User {user_id}")
    fig, ax = plt.subplots(figsize=(5,5))
    ax.plot(user_data["ActivityDate"], user_data["Calories"], marker="o", linestyle="-", color="red")
    ax.set_xlabel("Date")
    ax.set_ylabel("Calories Burnt")
    ax.set_title("Daily Calories Burnt")
    plt.xticks(rotation=45)
    with col6:
        st.pyplot(fig)

    st.subheader(f"Steps Over Time for User {user_id}")
    fig, ax = plt.subplots(figsize=(5,5))
    ax.plot(user_data["ActivityDate"], user_data["TotalSteps"], marker="o", linestyle="-", color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Steps")
    ax.set_title("Daily Steps")
    plt.xticks(rotation=45)
    with col7:
        st.pyplot(fig)

    start_date = pd.to_datetime("2016-03-12")
    end_date = pd.to_datetime("2016-09-04")

    selected_date = st.date_input(
        "Select a Date",
        value=start_date,  # Default to the start date
        min_value=start_date,
        max_value=end_date
    )
    session = st.text_input("nth session")
    date = selected_date.strftime("%#m/%#d/%Y")
    col8, col9 = st.columns(2)
    if selected_date:
        with col8:
            fig = plot_total_intensity(fetch_table_data("hourly_intensity", use_modified=True), user_id, date)
            st.pyplot(fig)
        with col9:
            if session:
                fig = plot_heart_rate(heart_rate_data, user_id, date , session)
                st.pyplot(fig)


# =================== Time-based Analysis ===================
elif page == "⏳ Time-based Analysis":
    st.title("Time-Based Activity Analysis")



# =================== Sleep Analysis ===================
elif page == "💤 Sleep Analysis":
    st.title("📈 Sleep Duration Regression Analysis")
    db_path = "data/fitbit_database_modified.db"
    conn = connect_to_db(db_path)

    # Load & Merge
    sleep_df = get_sleep_minutes_per_day(conn)
    activity_df = get_daily_activity_with_active_minutes(conn)
    merged_df = prepare_merged_data(sleep_df, activity_df)

    # === Sidebar Filters ===
    st.sidebar.header("Filter Options")
    user_ids = merged_df["Id"].unique()
    selected_id = st.sidebar.selectbox("Select User ID (or view all)", options=["All"] + sorted(user_ids.tolist()))

    activity_options = [
        "TotalActiveMinutes",
        "SedentaryMinutes",
        "VeryActiveMinutes",
        "FairlyActiveMinutes",
        "LightlyActiveMinutes"
    ]
    selected_predictor = st.sidebar.selectbox("Select Predictor Variable", activity_options)

    # Filter data
    if selected_id != "All":
        filtered_df = merged_df[merged_df["Id"] == selected_id]
    else:
        filtered_df = merged_df.copy()

    if filtered_df.empty:
        st.warning("No data available for the selected user.")
    else:
        # Run regression
        X = sm.add_constant(filtered_df[selected_predictor])
        y = filtered_df["asleep_minutes"]
        model = sm.OLS(y, X).fit()

        # === Key Regression Metrics ===
        st.subheader("📋 Key Regression Metrics")
        r2 = model.rsquared
        adj_r2 = model.rsquared_adj
        coef_df = pd.DataFrame({
            "Predictor": model.params.index,
            "Coefficient": model.params.values,
            "P-value": model.pvalues.values
        }).reset_index(drop=True)

        coef_df = coef_df[coef_df["Predictor"] != "const"]
        significant = coef_df[coef_df["P-value"] < 0.05]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("R-squared", f"{r2:.4f}")
            st.metric("Adjusted R-squared", f"{adj_r2:.4f}")
        with col2:
            if not significant.empty:
                st.success("✅ Significant Predictors:")
                for _, row in significant.iterrows():
                    st.write(f"- **{row['Predictor']}**: coef = `{row['Coefficient']:.2f}`, p = `{row['P-value']:.4f}`")
            else:
                st.error("No significant predictors (p ≥ 0.05)")

        # === Scatter Plot with Regression Line ===
        st.subheader(f"📈 Sleep Duration vs {selected_predictor}")
        fig1, ax1 = plt.subplots()
        sns.scatterplot(data=filtered_df, x=selected_predictor, y="asleep_minutes", ax=ax1, alpha=0.6)
        sorted_X = pd.DataFrame({selected_predictor: sorted(filtered_df[selected_predictor]), "const": 1})
        y_pred = model.predict(sorted_X[["const", selected_predictor]])
        ax1.plot(sorted_X[selected_predictor], y_pred, color="red", label="Regression Line")
        ax1.set_xlabel(selected_predictor)
        ax1.set_ylabel("Minutes Asleep")
        ax1.set_title(f"Sleep vs {selected_predictor}")
        ax1.legend()
        st.pyplot(fig1)

        # === Residual Diagnostics ===
        st.subheader("🧪 Residual Diagnostics")
        residuals = model.resid
        col3, col4 = st.columns(2)
        with col3:
            fig2, ax2 = plt.subplots()
            sns.histplot(residuals, kde=True, bins=30, ax=ax2)
            ax2.set_title("Histogram of Residuals")
            st.pyplot(fig2)
        with col4:
            fig3 = plt.figure()
            stats.probplot(residuals, dist="norm", plot=plt)
            plt.title("Q-Q Plot of Residuals")
            st.pyplot(fig3)

        # === Comparison: All Activity Types Together ===
        st.markdown("---")
        st.subheader("📊 Comparison of Activity Types (Multi-variable Regression)")

        # Run multi-variable regression
        X_multi = filtered_df[["VeryActiveMinutes", "FairlyActiveMinutes", "LightlyActiveMinutes"]]
        X_multi = sm.add_constant(X_multi)
        y_multi = filtered_df["asleep_minutes"]
        multi_model = sm.OLS(y_multi, X_multi).fit()

        coef_df = pd.DataFrame({
            "Predictor": multi_model.params.index,
            "Coefficient": multi_model.params.values,
            "P-value": multi_model.pvalues.values
        }).reset_index(drop=True)

        # Remove intercept
        coef_df = coef_df[coef_df["Predictor"] != "const"]
        coef_df["Significant"] = coef_df["P-value"] < 0.05

        # Bar plot of coefficients
        fig_bar, ax_bar = plt.subplots()
        sns.barplot(
            data=coef_df,
            x="Coefficient",
            y="Predictor",
            hue="Significant",
            dodge=False,
            palette={True: "green", False: "gray"},
            ax=ax_bar
        )
        ax_bar.set_title("Effect of Activity Types on Sleep Duration")
        ax_bar.set_xlabel("Coefficient (Effect on Minutes Asleep)")
        ax_bar.set_ylabel("Activity Type")
        st.pyplot(fig_bar)

  
# =================== Weather & Activity ===================
elif page == "🌦️ Weather & Activity":
    #test
    def load_user_selection():
        st.sidebar.header("Select Data")
        user_ids = merged_df["Id"].unique().tolist()
        user_id = st.sidebar.selectbox("Select User ID", user_ids, index=0)
        selected_blocks = st.sidebar.multiselect("Select Time Blocks", ["0-4", "4-8", "8-12", "12-16", "16-20", "20-24"], default=["8-12", "12-16", "16-20"])
        y_variable = st.sidebar.selectbox("Select Target Variable", ["StepTotal", "Calories", "TotalIntensity"], index=0)
        x_variables = st.sidebar.multiselect("Select Weather Variables", ["temp", "temp_squared", "precip"], default=["temp"])
        return user_id, selected_blocks, y_variable, x_variables

    def filter_data(user_id, selected_blocks):
        filtered_df = merged_df[merged_df["TimeBlock"].isin(selected_blocks)]
        filtered_df["temp_squared"] = filtered_df["temp"] ** 2
        user_specific_df = filtered_df[filtered_df["Id"] == user_id]
        return filtered_df, user_specific_df

    def summarize_regression_results(model, y_variable, x_variables):
        if not x_variables:
            st.error("No weather variables were selected. Please choose at least one variable for regression analysis.")
            return
        
        r_squared = model.rsquared
        adj_r_squared = model.rsquared_adj
        
        coef_df = pd.DataFrame({
            "Predictor": model.params.index,
            "Coefficient": model.params.values,
            "P-value": model.pvalues.values
        })
        coef_df = coef_df[coef_df["Predictor"] != "const"]
        
        significant_predictors = coef_df[coef_df["P-value"] < 0.05]
        
        st.write(f"Weather Variables Used: {', '.join(x_variables)}")
        
        if r_squared < 0.1:
            st.warning(f"The model has a very low R-squared value ({r_squared:.4f}), indicating that the weather variables do not significantly explain the variance in `{y_variable}`.")
        else:
            st.success(f"The model has an R-squared value of {r_squared:.4f}, indicating that the weather variables moderately explain the variance in `{y_variable}`.")
        
        if not significant_predictors.empty:
            significant_vars = ', '.join(significant_predictors['Predictor'].values)
            st.success(f"Significant Predictors (P-value < 0.05): {significant_vars}.")
        else:
            st.error("None of the selected weather variables are statistically significant (P-value ≥ 0.05).")

    def display_general_regression(filtered_df, selected_blocks, y_variable, x_variables):
        if not x_variables:
            st.error("No weather variables selected. Please choose at least one variable.")
            return

        st.subheader("General Regression Analysis With All Users")
        col1, col2 = st.columns([1, 1])
        with col1:
            print(f"run_regression function source: {run_regression.__module__}")
            model = run_weather_regression_(filtered_df, y_variable=y_variable, x_variables=x_variables, selected_blocks=selected_blocks)
            if model:
                summarize_regression_results(model, y_variable, x_variables)
        with col2:
            for x_variable in x_variables:
                fig1 = plot_general_weather_analysis(filtered_df, y_variable=y_variable, x_variable=x_variable, selected_blocks=selected_blocks)
                if fig1:
                    st.pyplot(fig1)


    def display_user_specific_analysis(user_specific_df, user_id, selected_blocks, y_variable, x_variables):
        st.subheader(f"User-Specific Regression Analysis for User {user_id}")
        col1, col2 = st.columns([1, 1])
        with col1:
            print(f"run_regression function source: {run_regression.__module__}")
            model = run_weather_regression_(user_specific_df, y_variable=y_variable, x_variables=x_variables, selected_blocks=selected_blocks)
            if model:
                summarize_regression_results(model, y_variable, x_variables)
        with col2:
            for x_variable in x_variables:
                fig2 = plot_user_weather_analysis(user_specific_df, user_id=user_id, y_variable=y_variable, x_variable=x_variable, selected_blocks=selected_blocks)
                if fig2:
                    st.pyplot(fig2)

    def main():
        st.title("Weather Impact on Activity")
        user_id, selected_blocks, y_variable, x_variables = load_user_selection()
        
        filtered_df, user_specific_df = filter_data(user_id, selected_blocks)
        if filtered_df.empty:
            st.warning(f"No data found in selected time blocks.")
        else:
            display_general_regression(filtered_df, selected_blocks, y_variable, x_variables)
            st.markdown("---")
            display_user_specific_analysis(user_specific_df, user_id, selected_blocks, y_variable, x_variables)

    if __name__ == "__main__":
        main()






