import pandas as pd
import datetime
import random  # For a little bit of variance, making it more realistic

# --- Configuration for Sample Data Generation ---

# Define the start date for your sample workout history
# Setting it earlier so you have some progress to view.
START_DATE = datetime.date(2025, 2, 1)  # Example: Start on May 1st, 2025

# Number of weeks for the sample plan
NUM_WEEKS = 16  # This will generate 8 weeks of data

# Base weights (in kg) for exercises. Adjust these as needed for realism.
BASE_WEIGHTS = {
    "Barbell Bench Press": 40.0,
    "Incline Dumbbell Press": 15.0,  # Per dumbbell
    "Dumbbell Fly": 10.0,
    "Push Ups": 0.0,  # Bodyweight, might log 0kg, so adjust display in app if needed
    "Barbell Squat": 50.0,
    "Leg Press": 80.0,
    "Romanian Deadlift": 30.0,
    "Leg Extension": 20.0,
    "Calf Raises": 30.0,
    "Pull Ups": 0.0,  # Bodyweight, might log 0kg, or use a "weight" for weighted pull-ups
    "Barbell Row": 35.0,
    "Seated Cable Row": 30.0,
    "Face Pulls": 10.0,
    "Overhead Press": 20.0,
    "Lateral Raise": 5.0,
    "Dumbbell Bicep Curl": 8.0,
    "Tricep Pushdown": 15.0,
    "Hammer Curls": 7.0
}

# Target rep range for each set
TARGET_REPS_MIN = 8
TARGET_REPS_MAX = 12

# How often to increase weight/reps (e.g., every 2 weeks)
PROGRESSION_INTERVAL_WEEKS = 2
WEIGHT_INCREASE_PER_INTERVAL = 2.5  # kg
REP_INCREASE_PER_INTERVAL = 1  # reps (if not increasing weight)

# --- End Configuration ---

# Define the workout plan for each day (same as before)
WORKOUT_PLAN = {
    "Monday": {
        "category": "Chest",
        "exercises": [
            "Barbell Bench Press",
            "Incline Dumbbell Press",
            "Dumbbell Fly",
            "Push Ups"
        ]
    },
    "Tuesday": {
        "category": "Legs",
        "exercises": [
            "Barbell Squat",
            "Leg Press",
            "Romanian Deadlift",
            "Leg Extension",
            "Calf Raises"
        ]
    },
    "Thursday": {
        "category": "Back",
        "exercises": [
            "Pull Ups",
            "Barbell Row",
            "Seated Cable Row",
            "Face Pulls"
        ]
    },
    "Friday": {
        "category": "Shoulders",  # Will be used for both shoulders and arms
        "exercises": [
            "Overhead Press",
            "Lateral Raise",
            "Dumbbell Bicep Curl",
            "Tricep Pushdown",
            "Hammer Curls"
        ]
    }
}

# Initialize an empty list to store workout rows
workout_rows = []

# Generate workouts for NUM_WEEKS
for week in range(NUM_WEEKS):
    for day_offset in range(7):  # Iterate through 7 days of the week
        current_date_for_loop = START_DATE + datetime.timedelta(weeks=week, days=day_offset)
        day_of_week = current_date_for_loop.strftime("%A")  # Get full weekday name

        if day_of_week in WORKOUT_PLAN:
            category = WORKOUT_PLAN[day_of_week]["category"]
            exercises = WORKOUT_PLAN[day_of_week]["exercises"]

            for exercise in exercises:
                # Calculate current weight and reps based on progression
                base_weight = BASE_WEIGHTS.get(exercise, 0.0)  # Get base, default to 0 if not found

                # Simple linear progression: increase weight every PROGRESSION_INTERVAL_WEEKS
                weight_increase = (week // PROGRESSION_INTERVAL_WEEKS) * WEIGHT_INCREASE_PER_INTERVAL
                current_weight = base_weight + weight_increase

                # Ensure reps stay within target range, maybe vary slightly
                current_reps = random.randint(TARGET_REPS_MIN, TARGET_REPS_MAX)

                # For bodyweight exercises like Push Ups/Pull Ups, keep weight at 0 or a nominal value
                if exercise in ["Push Ups", "Pull Ups"]:
                    current_weight = 0.0  # Log 0kg for bodyweight exercises unless weighted
                    # Reps can still increase for bodyweight exercises
                    rep_increase = (week // PROGRESSION_INTERVAL_WEEKS) * REP_INCREASE_PER_INTERVAL
                    current_reps = max(current_reps, TARGET_REPS_MIN + rep_increase)  # Ensure reps increase

                # Add 3 sets for each exercise
                for set_num in range(1, 4):  # 3 sets
                    workout_rows.append({
                        "date": current_date_for_loop.isoformat(),  # YYYY-MM-DD format
                        "category": category,
                        "exercise": exercise,
                        "weight": current_weight,
                        "reps": current_reps
                    })

# Create a DataFrame
df_workout_plan = pd.DataFrame(workout_rows)

# Save to CSV
OUTPUT_FILE = "predefined_workouts_with_data.csv"  # Changed filename to distinguish
df_workout_plan.to_csv(OUTPUT_FILE, index=False)

print(f"Pre-defined workout plan with sample data generated and saved to {OUTPUT_FILE}")
print(f"Total entries: {len(df_workout_plan)}")

# Display a few rows for verification
print("\nFirst 10 rows of the generated CSV:")
print(df_workout_plan.head(10))

print("\nLast 10 rows of the generated CSV:")
print(df_workout_plan.tail(10))