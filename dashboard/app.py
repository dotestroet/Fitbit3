import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.database_queries import fetch_table_data, get_table_names, save_table_data
from scripts.graphs import *
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
    st.title("Sleep Duration Analysis")



# =================== Weather & Activity ===================
elif page == "🌦️ Weather & Activity":
    st.title("Weather Impact on Activity")
