import pandas as pd

# Cleans the OLDER (2017-18) US trending dataset, "USvideos.csv" (columns: views, publish_time, ...).
# Earlier iteration of the project; the final dashboard uses the newer US_youtube_trending_data.csv.
df = pd.read_csv("data/USvideos.csv")

# ✅ Add a country column
df['country'] = 'US'

# ✅ Convert publish_time to datetime
df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce')

# ✅ Remove rows with missing required fields
df = df.dropna(subset=['video_id', 'title', 'views'])

# ✅ Clean text fields (remove newlines, trim spaces)
df['title'] = df['title'].str.replace(r'\n', ' ', regex=True).str.strip()
df['description'] = df['description'].fillna('').str.replace(r'\n', ' ', regex=True).str.strip()

# ✅ Optional: Remove emojis and special characters
df['title'] = df['title'].str.encode('ascii', 'ignore').str.decode('ascii')
df['description'] = df['description'].str.encode('ascii', 'ignore').str.decode('ascii')

# ✅ Save cleaned CSV for Snowflake
df.to_csv("data/clean_USvideos.csv", index=False)

print("✅ Preprocessing complete. File saved as data/clean_USvideos.csv")
