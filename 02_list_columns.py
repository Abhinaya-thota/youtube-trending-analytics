# Replace 'part_1.csv' with your actual CSV file path
csv_file_path = 'part_2.csv'

with open(csv_file_path, 'r', encoding='utf-8') as f:
    header_line = f.readline().strip()  # Read first line and remove trailing newline
    columns = header_line.split(',')    # Split by comma to get column names

print("Columns in CSV:")
for col in columns:
    print(col)
