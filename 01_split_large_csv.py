import os

input_file = "US_youtube_trending_data.csv"
output_prefix = "part_"
max_size_mb = 200  # each file < 250MB to be safe

# Get header
with open(input_file, 'r', encoding='utf-8') as f:
    header = f.readline()

file_count = 1
current_file = f"{output_prefix}{file_count}.csv"
current_size = 0

out = open(current_file, 'w', encoding='utf-8')
out.write(header)  # write header to first file

with open(input_file, 'r', encoding='utf-8') as f:
    next(f)  # skip header
    for line in f:
        line_size = len(line.encode('utf-8'))
        if (current_size + line_size) > (max_size_mb * 1024 * 1024):
            out.close()
            file_count += 1
            current_file = f"{output_prefix}{file_count}.csv"
            out = open(current_file, 'w', encoding='utf-8')
            out.write(header)
            current_size = 0
        out.write(line)
        current_size += line_size

out.close()
print(f"✅ Split complete: {file_count} files created.")
