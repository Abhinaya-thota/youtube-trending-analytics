"""
Reproduces the headline numbers from the analysis in pandas, straight from the raw US file,
so the findings can be checked without a Snowflake/Tableau connection.

Usage:  python findings_check.py [path/to/US_youtube_trending_data.csv]

Method: one row per video (its peak view count), engagement rate defined as in the Tableau
workbook: (likes + dislikes + comments) / views * 100. Publish day/hour are UTC (publishedAt).
"""
import sys
import pandas as pd

PATH = sys.argv[1] if len(sys.argv) > 1 else "data/US_youtube_trending_data.csv"

CATEGORIES = {1: "Film & Animation", 2: "Autos & Vehicles", 10: "Music", 15: "Pets & Animals",
              17: "Sports", 19: "Travel & Events", 20: "Gaming", 22: "People & Blogs",
              23: "Comedy", 24: "Entertainment", 25: "News & Politics", 26: "Howto & Style",
              27: "Education", 28: "Science & Technology", 29: "Nonprofits & Activism"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

cols = ["video_id", "categoryId", "publishedAt", "view_count", "likes", "dislikes", "comment_count"]
df = pd.read_csv(PATH, usecols=cols, low_memory=False)
print(f"{len(df):,} rows, {df.video_id.nunique():,} unique videos")

df = df[df.view_count > 0]
# one row per video: the row with its highest view count
v = df.sort_values("view_count").groupby("video_id").tail(1).copy()
v["engagement"] = (v.likes + v.dislikes + v.comment_count) / v.view_count * 100
v["category"] = v.categoryId.map(CATEGORIES)
v["published"] = pd.to_datetime(v.publishedAt, utc=True, errors="coerce")
v["weekday"] = v.published.dt.dayofweek
v["year"] = v.published.dt.year

cat = v.groupby("category").agg(videos=("engagement", "size"),
                                total_views_billions=("view_count", lambda s: s.sum() / 1e9),
                                mean_engagement=("engagement", "mean"))
cat = cat[cat.videos >= 200]
print("\nCategories ranked by total views (billions) and mean engagement rate (%):")
print(cat.sort_values("total_views_billions", ascending=False).round(2).to_string())

day = v.groupby("weekday").engagement.mean()
day.index = [DAYS[i] for i in day.index]
print("\nMean engagement rate (%) by publish day (UTC):")
print(day.round(2).to_string())

print("\nBest publish day, per year:")
for year, g in v.groupby("year"):
    by_day = g.groupby("weekday").engagement.mean()
    print(f"  {year}: {DAYS[by_day.idxmax()]} ({by_day.max():.2f}%)")
