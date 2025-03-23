import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import statsmodels.api as sm
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from scripts.database_queries import fetch_table_data, get_table_names, save_table_data
from scripts.graphs import *
from scripts.weather_analysis import merged_df, run_weather_regression_, plot_general_weather_analysis, plot_user_weather_analysis
from scripts.divide_the_day import convert_time_to_twentyfour_hours, assign_time_blocks
from scripts.sleep_analysis_modified import load_activity_data, load_sleep_data, merge_activity_sleep_data, run_regression

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
    merged_data = fetch_table_data("merged_heart_rate_activity", use_modified=True)

    merged_data['Date'] = pd.to_datetime(merged_data['Date']).dt.date
    total_users = merged_data["Id"].nunique()
    user_tracking_days = merged_data.groupby("Id")["Date"].nunique().reset_index()
    user_tracking_days.columns = ["Id", "TrackedDays"]

    user_tracking_days = user_tracking_days[user_tracking_days["TrackedDays"] >= 2]

    daily_summary = merged_data.groupby(["Id", "Date"]).agg(
        AvgHeartRate=("Value", "mean"),  
        AvgDailySteps=("TotalSteps", "mean"),
        AvgDailyCalories=("Calories", "mean"),
        AvgVeryActiveMinutes=("VeryActiveMinutes", "mean") 
    ).reset_index()

    daily_summary = daily_summary.merge(user_tracking_days, on="Id", how="left")
    
    daily_summary = daily_summary[daily_summary["TrackedDays"] >= 2]

    user_id = st.sidebar.selectbox("Select User ID", daily_summary["Id"].unique())
    user_data = daily_summary[daily_summary["Id"] == user_id]
    tracked_days = user_tracking_days[user_tracking_days["Id"] == user_id]["TrackedDays"].values[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Unique Individuals", total_users)
    with col2:
        st.metric("Tracked Days", tracked_days)
    with col3:
        st.metric("Average Heart Rate", round(user_data["AvgHeartRate"].mean(), 2))

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Average Daily Steps", round(user_data["AvgDailySteps"].mean(), 2))
    with col5:
        st.metric("Average Daily Calories Burnt", round(user_data["AvgDailyCalories"].mean(), 2))
    with col6:
        st.metric("Average Daily Very Active Minutes", round(user_data["AvgVeryActiveMinutes"].mean(), 2))

    st.subheader(f"Daily Summary for User {user_id}")
    st.dataframe(user_data)


    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Average Heart Rate Over Time for User {user_id}")
        fig, ax = plt.subplots()
        ax.plot(user_data["Date"], user_data["AvgHeartRate"], marker="o", linestyle="-", color="red")
        ax.set_xlabel("Date")
        ax.set_ylabel("Average Heart Rate")
        ax.set_title("Daily Average Heart Rate Over Time")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with col2:
        st.subheader(f"Average Daily Steps Over Time for User {user_id}")
        fig, ax = plt.subplots()
        ax.plot(user_data["Date"], user_data["AvgDailySteps"], marker="o", linestyle="-", color="blue")
        ax.set_xlabel("Date")
        ax.set_ylabel("Average Daily Steps")
        ax.set_title("Average Daily Steps Over Time")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with col1:
        st.subheader(f"Average Daily Calories Burnt Over Time for User {user_id}")
        fig, ax = plt.subplots()
        ax.plot(user_data["Date"], user_data["AvgDailyCalories"], marker="o", linestyle="-", color="green")
        ax.set_xlabel("Date")
        ax.set_ylabel("Average Daily Calories Burnt")
        ax.set_title("Average Daily Calories Burnt Over Time")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with col2:
        st.subheader(f"Average Daily Very Active Minutes Over Time for User {user_id}")
        fig, ax = plt.subplots()
        ax.plot(user_data["Date"], user_data["AvgVeryActiveMinutes"], marker="o", linestyle="-", color="purple")
        ax.set_xlabel("Date")
        ax.set_ylabel("Average Daily Very Active Minutes")
        ax.set_title("Average Daily Very Active Minutes Over Time")
        plt.xticks(rotation=45)
        st.pyplot(fig)


    # user_id = st.sidebar.selectbox("Select User ID", daily_activity["Id"].unique())

    # user_data = daily_activity[daily_activity["Id"] == user_id]
    # user_sleep_data = sleep_data[sleep_data["Id"] == user_id]
    # user_heart_rate_data = heart_rate_data[heart_rate_data["Id"] == user_id]
    # user_weight_data = weight_data[weight_data["Id"] == user_id]

    # total_steps = user_data["TotalSteps"].sum()
    # total_calories = user_data["Calories"].sum()
    # avg_steps = user_data["TotalSteps"].mean()
    # avg_calories = user_data["Calories"].mean()

    # #avg_resting_heart_rate = user_heart_rate_data["RestingHeartRate"].mean() if not user_heart_rate_data.empty else 0
    # avg_weight = user_weight_data["WeightKg"].mean() if not user_weight_data.empty else 0

    # col1, col2, col3, col4, col5 = st.columns(5)

    # with col1:
    #     st.metric("Total Steps", round(total_steps, 2))
    # with col2:
    #     st.metric("Total Calories Burnt", round(total_calories, 2))
    # with col3:
    #     st.metric("Average Steps Per Day", round(avg_steps, 2))
    # with col4:
    #     st.metric("Average Calories Burnt Per Day", round(avg_calories, 2))

    # if avg_weight > 0:
    #     with col5:
    #         st.metric("Average Weight (kg)", round(avg_weight, 2))

    # col6, col7 = st.columns(2)
    # st.subheader(f"Calories Burnt Over Time for User {user_id}")
    # fig, ax = plt.subplots(figsize=(5,5))
    # ax.plot(user_data["ActivityDate"], user_data["Calories"], marker="o", linestyle="-", color="red")
    # ax.set_xlabel("Date")
    # ax.set_ylabel("Calories Burnt")
    # ax.set_title("Daily Calories Burnt")
    # plt.xticks(rotation=45)
    # with col6:
    #     st.pyplot(fig)

    # st.subheader(f"Steps Over Time for User {user_id}")
    # fig, ax = plt.subplots(figsize=(5,5))
    # ax.plot(user_data["ActivityDate"], user_data["TotalSteps"], marker="o", linestyle="-", color="blue")
    # ax.set_xlabel("Date")
    # ax.set_ylabel("Total Steps")
    # ax.set_title("Daily Steps")
    # plt.xticks(rotation=45)
    # with col7:
    #     st.pyplot(fig)




# =================== Time-based Analysis ===================
elif page == "⏳ Time-based Analysis":
    st.title("Time-Based Activity Analysis")
    

    heart_rate_data = fetch_table_data("heart_rate", use_modified=True)
    merged_data = fetch_table_data("hourly_intensity", use_modified=True)
    daily_activity = fetch_table_data("daily_activity", use_modified=True)
    user_id = st.sidebar.selectbox("Select User ID", daily_activity["Id"].unique())

    start_date = pd.to_datetime("2016-03-12")
    end_date = pd.to_datetime("2016-09-04")

    selected_date = st.date_input(
        "Select a Date",
        value=start_date, 
        min_value=start_date,
        max_value=end_date
    )
    session = st.text_input("nth session")
    date = selected_date.strftime("%#m/%#d/%Y")


    col8, col9 = st.columns(2)
    if selected_date:
        with col8:
            fig = plot_total_intensity(merged_data, user_id, date)
            st.pyplot(fig)
        with col9:
            if session:
                fig = plot_heart_rate(heart_rate_data, user_id, date , session)
                st.pyplot(fig) 



# =================== Sleep Analysis ===================
elif page == "💤 Sleep Analysis":
    st.title("Sleep Duration Analysis")
    st.write("This section analyzes how individuals' activity levels affect their sleep durations.")


    activity_df = load_activity_data()  
    sleep_df = load_sleep_data() 
    merged_df = merge_activity_sleep_data(activity_df, sleep_df)  


    st.subheader("⚙️ Select Variable to Analyze Against Sleep Duration")
    variable_options = ["TotalActiveMinutes", "VeryActiveMinutes", "FairlyActiveMinutes", "LightlyActiveMinutes"]
    selected_variable = st.selectbox("Choose an activity variable:", variable_options)


    X = merged_df[selected_variable]  
    y = merged_df["TotalMinutesAsleep"]  
    X_const = sm.add_constant(X)  
    model = sm.OLS(y, X_const).fit()  

  
    st.subheader("📋 Regression Summary")
    st.text(model.summary())


    st.subheader("📈 Scatter Plot with Regression Line")
    fig, ax = plt.subplots()
    sns.regplot(x=X, y=y, ax=ax, line_kws={"color": "red"})  
    ax.set_xlabel(selected_variable)  
    ax.set_ylabel("Total Minutes Asleep") 
    ax.set_title(f"{selected_variable} vs Sleep Duration") 
    st.pyplot(fig)  

  
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






