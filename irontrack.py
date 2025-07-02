import streamlit as st
import pandas as pd
import os
import datetime
from io import BytesIO


DATA_FILENAME = "predefined_workouts_with_data.csv"

DEFAULT_CATEGORIES = {
    "Chest": ["Barbell Bench Press", "Dumbbell Fly"],
    "Back": ["Pull Ups", "Barbell Row"],
    "Arms": ["Dumbbell Curls", "Tricep Pushdown"],
    "Legs": ["Squat", "Leg Press"],
    "Shoulders": ["Shoulder Press", "Lateral Raise"]
}




def get_data_file_path():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    return os.path.join(parent_dir, DATA_FILENAME)


@st.cache_data(ttl=1)  # Cache for 1 second to ensure frequent re-reads
def load_data():
    """
    Loads workout data from the CSV file.
    Ensures column types are correct and handles missing file errors.
    """
    data_file_abs_path = get_data_file_path()
    try:
        df = pd.read_csv(data_file_abs_path)
        # Ensure 'date' column is consistently a string for comparison
        df['date'] = df['date'].astype(str)
        # Ensure 'weight' and 'reps' are numeric, handling potential errors and filling NaNs
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(0.0)
        df['reps'] = pd.to_numeric(df['reps'], errors='coerce').fillna(0).astype(int)
        return df
    except FileNotFoundError:
        st.error(f"Error: Data file not found at {data_file_abs_path}. Please ensure it exists and is named correctly.")
        return pd.DataFrame(columns=["date", "category", "exercise", "weight", "reps"])
    except Exception as e:
        st.error(f"An unexpected error occurred while loading data from {data_file_abs_path}: {e}")
        return pd.DataFrame(columns=["date", "category", "exercise", "weight", "reps"])


def save_data(df):
    """Saves the DataFrame to the CSV file."""
    data_file_abs_path = get_data_file_path()
    try:
        df.to_csv(data_file_abs_path, index=False)
        # Invalidate the cache after saving so load_data will get fresh data on next call
        load_data.clear()
    except Exception as e:
        st.error(f"An error occurred while saving data to {data_file_abs_path}: {e}")


def log_set(date, category, exercise, weight, reps):
    """Adds a new workout set to the DataFrame and saves it."""
    df = load_data()  # Load current data (might be cached)
    new_row = pd.DataFrame([{
        "date": date,
        "category": category,
        "exercise": exercise,
        "weight": float(weight),
        "reps": int(reps)
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)  # Save data, which will clear the cache


def get_unique_categories():
    """Retrieves all unique categories from the data and default categories."""
    df = load_data()
    all_categories = set(df["category"].dropna().unique()).union(DEFAULT_CATEGORIES.keys())
    return sorted(list(all_categories))


def get_exercises_for_category(category):
    """Retrieves all exercises for a given category from data and default categories."""
    df = load_data()
    custom_exercises = df[df["category"] == category]["exercise"].dropna().unique().tolist()
    default_exercises = DEFAULT_CATEGORIES.get(category, [])
    return sorted(list(set(default_exercises + custom_exercises)))


# --- Visualization-Specific Data Processing Functions ---

# Helper function to prepare data for progress charts (Weight, Reps, Volume)
def get_exercise_progress_data(df, selected_exercise):
    df_filtered = df[(df["exercise"] == selected_exercise) & (df["reps"] > 0)].copy()
    if df_filtered.empty:
        return pd.DataFrame()
    df_filtered["date"] = pd.to_datetime(df_filtered["date"])
    df_filtered['volume'] = df_filtered['weight'] * df_filtered['reps']
    # Group by date and sum for daily/workout totals
    daily_progress = df_filtered.groupby('date').agg({
        'reps': 'sum',
        'weight': 'sum',  # Sum of weight per day might be less useful, consider max or average
        'volume': 'sum'
    }).reset_index()
    return daily_progress.sort_values('date')


def get_workout_consistency_data(df, period='Week'):
    """Calculates workout consistency by counting unique days per period."""
    df_logged = df[df['reps'] > 0].copy()  # Only consider actual logged workouts
    if df_logged.empty:
        return pd.DataFrame()

    df_logged['date'] = pd.to_datetime(df_logged['date'])
    if period == 'Week':
        df_logged['period'] = df_logged['date'].dt.to_period('W').astype(str)
    elif period == 'Month':
        df_logged['period'] = df_logged['date'].dt.to_period('M').astype(str)
    else:  # Default to Week if unknown period
        df_logged['period'] = df_logged['date'].dt.to_period('W').astype(str)

    consistency_df = df_logged.groupby('period')['date'].nunique().reset_index(name='Workout Days')
    return consistency_df.sort_values('period')


def get_category_distribution_data(df, metric='Total Volume'):
    """Calculates distribution of workouts by category based on sets or volume."""
    df_logged = df[df['reps'] > 0].copy()
    if df_logged.empty:
        return pd.DataFrame()

    if metric == 'Number of Sets':
        category_data = df_logged.groupby('category').size().reset_index(name='Count')
        category_data = category_data.sort_values('Count', ascending=False)
    elif metric == 'Total Volume':
        df_logged['volume'] = df_logged['weight'] * df_logged['reps']
        category_data = df_logged.groupby('category')['volume'].sum().reset_index(name='Total Volume')
        category_data = category_data.sort_values('Total Volume', ascending=False)
    else:
        return pd.DataFrame()  # Should not happen with dropdown

    return category_data


def get_top_exercises_data(df, top_n=5, metric='Total Volume'):
    """Calculates top N exercises based on total sets or total volume."""
    df_logged = df[df['reps'] > 0].copy()
    if df_logged.empty:
        return pd.DataFrame()

    if metric == 'Number of Sets':
        exercise_counts = df_logged.groupby('exercise').size().reset_index(name='Count')
        top_exercises = exercise_counts.sort_values('Count', ascending=False).head(top_n)
    elif metric == 'Total Volume':
        df_logged['volume'] = df_logged['weight'] * df_logged['reps']
        exercise_volumes = df_logged.groupby('exercise')['volume'].sum().reset_index(name='Total Volume')
        top_exercises = exercise_volumes.sort_values('Total Volume', ascending=False).head(top_n)
    else:
        return pd.DataFrame()  # Should not happen

    return top_exercises


# --- Initialize Data File if it doesn't exist ---
DATA_FILE_ABS_PATH_INIT = get_data_file_path()

if not os.path.exists(DATA_FILE_ABS_PATH_INIT):
    st.warning(f"Data file '{DATA_FILE_ABS_PATH_INIT}' not found. Initializing with default categories.")
    df_init = pd.DataFrame(columns=["date", "category", "exercise", "weight", "reps"])
    rows = []
    for cat, exs in DEFAULT_CATEGORIES.items():
        for ex in exs:
            rows.append({
                "date": datetime.date.today().isoformat(),
                "category": cat,
                "exercise": ex,
                "weight": 0.0,
                "reps": 0
            })
    df_init = pd.concat([df_init, pd.DataFrame(rows)], ignore_index=True)
    df_init.to_csv(DATA_FILE_ABS_PATH_INIT, index=False)

# --- Streamlit UI Layout ---
st.set_page_config(page_title="IronTracker", layout="wide")
st.title("🏋️ IronTracker - Workout Logger")

# Sidebar Navigation
menu = st.sidebar.radio("Navigate", ["Log Workout", "View Workouts", "Add Custom Exercise", "View Progress"])

# Export All Logs Section in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📤 Export All Logs")
df_export = load_data()
csv_data = df_export.to_csv(index=False).encode("utf-8")
st.sidebar.download_button("Download CSV", csv_data, "workout_log.csv", mime="text/csv")
excel_buffer = BytesIO()
df_export.to_excel(excel_buffer, index=False, engine="openpyxl")
st.sidebar.download_button("Download Excel", excel_buffer.getvalue(), "workout_log.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Date Navigation for Log Workout (shared)
today = datetime.date.today()
if "log_date" not in st.session_state:
    st.session_state["log_date"] = today

col1, col2, col3, col4 = st.columns([1, 4, 1, 1])
with col1:
    if st.button("⬅️ Previous Day", key="prev_day_btn"):
        st.session_state["log_date"] -= datetime.timedelta(days=1)
with col3:
    if st.button("➡️ Next Day", key="next_day_btn"):
        st.session_state["log_date"] += datetime.timedelta(days=1)
with col4:
    if st.button("📅 Today", key="today_btn"):
        st.session_state["log_date"] = today

# --- Log Workout Section ---
if menu == "Log Workout":
    st.subheader("📆 Log Workout")
    log_date = st.date_input("Select Date", st.session_state["log_date"], key="date_picker")
    category = st.selectbox("Select Category", ["Select"] + get_unique_categories(), index=0, key="log_category_select")

    if category != "Select":
        search_query = st.text_input("🔍 Search Exercise", key="log_search_query").lower()
        exercises = get_exercises_for_category(category)
        filtered_exercises = [ex for ex in exercises if search_query in ex.lower()]

        exercise = st.selectbox("Select Exercise", filtered_exercises, key="log_exercise_select")

        if exercise:
            tab1, tab2, tab3 = st.tabs(["➕ Track Set", "📜 Past Sets", "📈 Basic Progress"])

            with tab1:
                weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5, format="%.1f", key="log_weight_input")
                reps = st.number_input("Reps", min_value=1, step=1, key="log_reps_input")
                if st.button("Save Set", key="save_set_btn"):
                    log_set(log_date.isoformat(), category, exercise, weight, reps)
                    st.success(f"✅ Saved: {reps} reps @ {weight}kg for {exercise} on {log_date}")

            with tab2:
                df = load_data()
                hist = df[(df["exercise"] == exercise) & (df["reps"] > 0)]
                hist = hist.sort_values("date", ascending=False)
                if hist.empty:
                    st.info("No past workouts found for this exercise.")
                else:
                    st.markdown("#### Past Sets for This Exercise")
                    for d in hist["date"].unique():
                        st.markdown(f"**{d}**")
                        sets_on_date = hist[hist["date"] == d]
                        for _, row in sets_on_date.iterrows():
                            st.write(f"{int(row['reps'])} reps @ {row['weight']}kg")

            with tab3:
                # Basic progress graphs (weight and reps) for the selected exercise
                df_plot = load_data()
                df_plot_filtered = df_plot[(df_plot["exercise"] == exercise) & (df_plot["reps"] > 0)].copy()

                if df_plot_filtered.empty:
                    st.info("No data to plot for this exercise.")
                else:
                    df_plot_filtered["date"] = pd.to_datetime(df_plot_filtered["date"])
                    st.markdown("##### Reps Over Time")
                    st.line_chart(df_plot_filtered.set_index("date")["reps"], use_container_width=True)
                    st.markdown("##### Weight Over Time")
                    st.line_chart(df_plot_filtered.set_index("date")["weight"], use_container_width=True)


# --- View Workouts Section ---
elif menu == "View Workouts":
    st.subheader("📅 View Workouts By Date")
    selected_date = st.date_input("Pick a Date to View", today, key="view_date_picker")
    df = load_data()

    df_day = df[df["date"] == str(selected_date)]

    if df_day.empty:
        st.info("No workouts found for this date. Try navigating to an earlier date like 2025-05-01.")
    else:
        st.markdown("### 🔽 Download This Day's Workouts")
        csv_day = df_day.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv_day, f"workouts_{selected_date}.csv", mime="text/csv")
        excel_day_buffer = BytesIO()
        df_day.to_excel(excel_day_buffer, index=False, engine="openpyxl")
        st.download_button("Download Excel", excel_day_buffer.getvalue(), f"workouts_{selected_date}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        for cat in df_day["category"].unique():
            st.markdown(f"### {selected_date} - {cat}")
            for ex in df_day[df_day["category"] == cat]["exercise"].unique():
                st.markdown(f"**{ex}**")
                sets_for_display = df_day[(df_day["category"] == cat) & (df_day["exercise"] == ex)]
                for _, row in sets_for_display.iterrows():
                    display_reps = f"{int(row['reps'])} reps" if row['reps'] > 0 else "N/A reps"
                    display_weight = f"{row['weight']}kg" if row['weight'] > 0 else "N/A weight"

                    st.write(f"{display_reps} @ {display_weight}")

# --- Add Custom Exercise Section ---
elif menu == "Add Custom Exercise":
    st.subheader("➕ Add Your Own Exercise")
    new_cat = st.text_input("Enter Category (e.g., Arms, Chest, etc.)", key="new_cat_input").strip().title()
    new_ex = st.text_input("Enter Exercise Name", key="new_ex_input").strip().title()

    if st.button("Save Exercise"):
        if new_cat and new_ex:
            log_set(today.isoformat(), new_cat, new_ex, 0.0, 0)
            st.success(f"✅ Custom exercise '{new_ex}' added to category '{new_cat}'!")
            st.session_state["new_cat_input"] = ""
            st.session_state["new_ex_input"] = ""
        else:
            st.error("Please enter both category and exercise name.")

# --- View Progress Section (Enhanced with multiple visualizations) ---
elif menu == "View Progress":
    st.subheader("📈 Analyze Your Progress")
    df_all_data = load_data()  # Load data once for this section

    if df_all_data.empty or df_all_data[df_all_data['reps'] > 0].empty:
        st.info("No actual workout data available to analyze progress. Log some workouts first!")
    else:
        visualization_type = st.selectbox(
            "Select a Visualization Type",
            [
                "--- Select ---",
                "Weight, Reps & Volume Progress for an Exercise",
                "Workout Consistency (Days per Period)",
                "Exercise Category Distribution",
                "Top Performed Exercises"
            ],
            key="viz_type_select"
        )

        if visualization_type == "Weight, Reps & Volume Progress for an Exercise":
            st.markdown("#### Weight, Reps & Volume Over Time for an Exercise")
            all_exercises = sorted(df_all_data["exercise"].dropna().unique())
            selected_exercise = st.selectbox("Select Exercise", all_exercises, key="viz_exercise_select")

            if selected_exercise:
                progress_data = get_exercise_progress_data(df_all_data, selected_exercise)
                if progress_data.empty:
                    st.info(f"No actual logged data to show progress for '{selected_exercise}'.")
                else:
                    st.markdown("##### Reps Over Time")
                    st.line_chart(progress_data.set_index("date")["reps"], use_container_width=True)
                    st.markdown("##### Weight Over Time")
                    st.line_chart(progress_data.set_index("date")["weight"], use_container_width=True)
                    st.markdown("##### Total Volume Over Time (Weight x Reps)")
                    st.line_chart(progress_data.set_index("date")["volume"], use_container_width=True)

        elif visualization_type == "Workout Consistency (Days per Period)":
            st.markdown("#### Workout Consistency Over Time")
            period_choice = st.radio("Group by:", ["Week", "Month"], key="consistency_period_radio")

            consistency_df = get_workout_consistency_data(df_all_data, period_choice)
            if consistency_df.empty:
                st.info("No data available to track workout consistency.")
            else:
                st.bar_chart(consistency_df.set_index('period')['Workout Days'], use_container_width=True)
                st.info(f"Shows the number of unique days you worked out per {period_choice.lower()}.")

        elif visualization_type == "Exercise Category Distribution":
            st.markdown("#### Distribution of Workouts by Category")
            metric_choice = st.radio("Measure by:", ["Number of Sets", "Total Volume"], key="category_metric_radio")

            category_data = get_category_distribution_data(df_all_data, metric_choice)
            if category_data.empty:
                st.info("No data available to show category distribution.")
            else:
                if metric_choice == 'Number of Sets':
                    st.bar_chart(category_data.set_index('category')['Count'], use_container_width=True)
                else:  # Total Volume
                    st.bar_chart(category_data.set_index('category')['Total Volume'], use_container_width=True)
                st.info(f"Shows workout distribution across categories based on {metric_choice.lower()}.")

        elif visualization_type == "Top Performed Exercises":
            st.markdown("#### Top Exercises by Sets or Volume")
            top_n = st.slider("Show Top N Exercises", min_value=1, max_value=10, value=5, step=1, key="top_n_slider")
            metric_choice_top = st.radio("Measure by:", ["Number of Sets", "Total Volume"],
                                         key="top_exercises_metric_radio")

            top_exercises = get_top_exercises_data(df_all_data, top_n, metric_choice_top)
            if top_exercises.empty:
                st.info("No data available to determine top exercises.")
            else:
                if metric_choice_top == 'Number of Sets':
                    st.bar_chart(top_exercises.set_index('exercise')['Count'], use_container_width=True)
                else:  # Total Volume
                    st.bar_chart(top_exercises.set_index('exercise')['Total Volume'], use_container_width=True)
                st.info(f"Shows your top {top_n} exercises based on {metric_choice_top.lower()}.")

        else:
            st.info("Select a visualization type from the dropdown above to get started!")

