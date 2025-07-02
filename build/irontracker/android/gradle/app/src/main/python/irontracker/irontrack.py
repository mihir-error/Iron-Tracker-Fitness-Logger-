import streamlit as st
import pandas as pd
import os
import datetime
from io import BytesIO

DATA_FILE = "../fitness_data.csv"

DEFAULT_CATEGORIES = {
    "Chest": ["Barbell Bench Press", "Dumbbell Fly"],
    "Back": ["Pull Ups", "Barbell Row"],
    "Arms": ["Dumbbell Curls", "Tricep Pushdown"],
    "Legs": ["Squat", "Leg Press"],
    "Shoulders": ["Shoulder Press", "Lateral Raise"]
}

# Initialize
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["date", "category", "exercise", "weight", "reps"])
    rows = []
    for cat, exs in DEFAULT_CATEGORIES.items():
        for ex in exs:
            rows.append({
                "date": datetime.date.today(),
                "category": cat,
                "exercise": ex,
                "weight": -1,
                "reps": -1
            })
    df_init = pd.concat([df_init, pd.DataFrame(rows)], ignore_index=True)
    df_init.to_csv(DATA_FILE, index=False)

# Helpers
def load_data():
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def log_set(date, category, exercise, weight, reps):
    df = load_data()
    new_row = pd.DataFrame([{
        "date": date,
        "category": category,
        "exercise": exercise,
        "weight": weight,
        "reps": reps
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)

def get_unique_categories():
    df = load_data()
    return sorted(set(df["category"].dropna().unique()).union(DEFAULT_CATEGORIES.keys()))

def get_exercises_for_category(category):
    df = load_data()
    custom = df[df["category"] == category]["exercise"].dropna().unique().tolist()
    default = DEFAULT_CATEGORIES.get(category, [])
    return sorted(set(default + custom))

# UI
st.set_page_config(page_title="IronTracker", layout="wide")
st.title("🏋️ IronTracker - Workout Logger")

menu = st.sidebar.radio("Navigate", ["Log Workout", "View Workouts", "Add Custom Exercise", "View Progress"])

# Export all logs
st.sidebar.markdown("---")
st.sidebar.markdown("### 📤 Export All Logs")
df_export = load_data()
csv_data = df_export.to_csv(index=False).encode("utf-8")
st.sidebar.download_button("Download CSV", csv_data, "workout_log.csv", mime="text/csv")
excel_buffer = BytesIO()
df_export.to_excel(excel_buffer, index=False, engine="openpyxl")
st.sidebar.download_button("Download Excel", excel_buffer.getvalue(), "workout_log.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Date navigation
today = datetime.date.today()
if "log_date" not in st.session_state:
    st.session_state["log_date"] = today

col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    if st.button("⬅️"):
        st.session_state["log_date"] -= datetime.timedelta(days=1)
with col3:
    if st.button("➡️"):
        st.session_state["log_date"] += datetime.timedelta(days=1)

# --------------- Log Workout ---------------
if menu == "Log Workout":
    st.subheader("📆 Log Workout")
    log_date = st.date_input("Select Date", st.session_state["log_date"], key="date_picker")
    category = st.selectbox("Select Category", ["Select"] + get_unique_categories(), index=0)

    if category != "Select":
        search_query = st.text_input("🔍 Search Exercise").lower()
        exercises = get_exercises_for_category(category)
        filtered_exercises = [ex for ex in exercises if search_query in ex.lower()]

        exercise = st.selectbox("Select Exercise", filtered_exercises)

        if exercise:
            tab1, tab2, tab3 = st.tabs(["➕ Track", "📜 Past Workouts", "📈 Graph"])

            with tab1:
                weight = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
                reps = st.number_input("Reps", min_value=1, step=1)
                if st.button("Save Set"):
                    log_set(log_date, category, exercise, weight, reps)
                    st.success(f"✅ Saved: {reps} reps @ {weight}kg for {exercise} on {log_date}")

            with tab2:
                df = load_data()
                hist = df[(df["exercise"] == exercise) & (df["reps"] != -1)]
                hist = hist.sort_values("date")
                if hist.empty:
                    st.info("No past workouts found.")
                else:
                    st.markdown("#### Past Sets")
                    for d in hist["date"].unique():
                        st.markdown(f"**{d}**")
                        sets = hist[hist["date"] == d]
                        for _, row in sets.iterrows():
                            st.write(f"{row['reps']} reps @ {row['weight']}kg")

            with tab3:
                df = load_data()
                df = df[(df["exercise"] == exercise) & (df["reps"] != -1)]
                if df.empty:
                    st.info("No data to plot.")
                else:
                    df["date"] = pd.to_datetime(df["date"])
                    df["reps"] = pd.to_numeric(df["reps"], errors='coerce')
                    df["weight"] = pd.to_numeric(df["weight"], errors='coerce')
                    st.line_chart(df.set_index("date")["reps"], use_container_width=True)
                    st.line_chart(df.set_index("date")["weight"], use_container_width=True)

# --------------- View Workouts ---------------
elif menu == "View Workouts":
    st.subheader("📅 View Workouts By Date")
    selected_date = st.date_input("Pick a Date to View", today)
    df = load_data()
    df_day = df[(df["date"] == str(selected_date)) & (df["reps"] != -1)]

    if df_day.empty:
        st.info("No workouts found for this date.")
    else:
        st.markdown("### 🔽 Download This Day's Workouts")
        csv_day = df_day.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv_day, f"workouts_{selected_date}.csv", mime="text/csv")
        excel_day = BytesIO()
        df_day.to_excel(excel_day, index=False, engine="openpyxl")
        st.download_button("Download Excel", excel_day.getvalue(), f"workouts_{selected_date}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        for cat in df_day["category"].unique():
            st.markdown(f"### {selected_date} - {cat}")
            for ex in df_day[df_day["category"] == cat]["exercise"].unique():
                st.markdown(f"**{ex}**")
                sets = df_day[(df_day["category"] == cat) & (df_day["exercise"] == ex)]
                for _, row in sets.iterrows():
                    st.write(f"{row['reps']} reps @ {row['weight']}kg")

# --------------- Add Custom Exercise ---------------
elif menu == "Add Custom Exercise":
    st.subheader("➕ Add Your Own Exercise")
    new_cat = st.text_input("Enter Category (e.g., Arms, Chest, etc.)")
    new_ex = st.text_input("Enter Exercise Name")

    if st.button("Save Exercise"):
        if new_cat and new_ex:
            log_set(today, new_cat.strip().title(), new_ex.strip().title(), -1, -1)
            st.success("✅ Custom exercise saved successfully!")
        else:
            st.error("Please enter both category and exercise name.")

# --------------- View Progress ---------------
elif menu == "View Progress":
    st.subheader("📈 Progress Over Time")
    all_exercises = sorted(load_data()["exercise"].dropna().unique())
    selected_exercise = st.selectbox("Select Exercise", all_exercises)

    df = load_data()
    df = df[(df["exercise"] == selected_exercise) & (df["reps"] != -1)]
    if df.empty:
        st.info("No data available for this exercise.")
    else:
        df["date"] = pd.to_datetime(df["date"])
        df["reps"] = pd.to_numeric(df["reps"], errors='coerce')
        df["weight"] = pd.to_numeric(df["weight"], errors='coerce')
        st.line_chart(df.set_index("date")["reps"], use_container_width=True)
        st.line_chart(df.set_index("date")["weight"], use_container_width=True)
