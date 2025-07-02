import json
import csv

# Load data from JSON file
with open("workout_data.json", "r") as json_file:
    data = json.load(json_file)

# Define CSV output file
csv_file = "view_workout_.csv"

# Define column headers based on keys in JSON
fieldnames = ["date", "category", "exercise", "weight", "reps"]

# Write CSV
with open(csv_file, "w", newline="") as csv_output:
    writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

print(f"✅ Converted JSON to CSV: {csv_file}")
