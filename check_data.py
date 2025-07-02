import pandas as pd
import os

# This path should match what your irontrack.py is using relative to its location
# If irontrack.py is in 'irontracker/' and data file is in 'fitness logger/', then path is '../predefined_workouts_with_data.csv'
# So, if you run THIS script from 'fitness logger/' as well, the path to data is direct.
# Let's assume you're running this from the *same directory* as 'generate_workouts.py' and the data file.
# If your 'predefined_workouts_with_data.csv' is directly in 'fitness logger/', then this path is correct.

DATA_FILE_PATH = "predefined_workouts_with_data.csv" # Direct path from 'fitness logger/'

print(f"Checking for file: {DATA_FILE_PATH}")

if os.path.exists(DATA_FILE_PATH):
    print("File found! Attempting to load data...")
    try:
        df = pd.read_csv(DATA_FILE_PATH)
        print("Data loaded successfully!")
        print(f"Total rows in DataFrame: {len(df)}")
        print("\nFirst 5 rows of loaded data:")
        print(df.head())
        print("\nUnique dates in loaded data:")
        print(df['date'].unique())

        # Check for the specific date 2025-05-01
        target_date = '2025-05-01'
        df_filtered = df[df['date'] == target_date]
        print(f"\nRows for {target_date}: {len(df_filtered)}")
        if not df_filtered.empty:
            print(f"Sample data for {target_date}:\n{df_filtered.head()}")

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        print("This usually means the CSV is malformed or pandas can't parse it.")
else:
    print(f"ERROR: File '{DATA_FILE_PATH}' not found at this location.")
    print("Please ensure 'predefined_workouts_with_data.csv' is in the same directory as this script.")
    print("Or adjust 'DATA_FILE_PATH' in this script if it's elsewhere.")