import csv
import json

# Load CSV data
def load_csv_data(filename):
    data = {}
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            pid = row['PID']
            if pid not in data or row['Source'] == 'Fitbit Return':
                data[pid] = {
                    'start_date': row['Start Date'],
                    'end_date': row['End Date']
                }
    return data

# Load the JSON data
def load_json_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)

# Update the JSON data
def update_json_data(json_data, csv_data):
    for pid, dates in csv_data.items():
        if pid in json_data:
            json_data[pid]['official_start_date'] = dates['start_date']
            json_data[pid]['official_end_date'] = dates['end_date']

# Save the updated JSON data
def save_json_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

csv_filename = 'pids.csv'
json_filename = 'fitbit_data_partial_80.json'

# Load, process, and update the data
csv_data = load_csv_data(csv_filename)
json_data = load_json_data(json_filename)
update_json_data(json_data, csv_data)
save_json_data(json_filename, json_data)

print("JSON file has been updated.")
