"""
Reproduces the headline numbers from the analysis in pandas, straight from the raw US file,
so the findings can be checked without a Snowflake/Tableau connection.

Usage:  python findings_check.py [path/to/US_youtube_trending_data.csv] [--min-videos 200]

Method: one row per video (its peak view count), engagement rate defined as in the Tableau
workbook: (likes + dislikes + comments) / views * 100. Publish day/hour are UTC (publishedAt).
"""
import argparse
import sys

import pandas as pd

CATEGORIES = {1: "Film & Animation", 2: "Autos & Vehicles", 10: "Music", 15: "Pets & Animals",
              17: "Sports", 19: "Travel & Events", 20: "Gaming", 22: "People & Blogs",
              23: "Comedy", 24: "Entertainment", 25: "News & Politics", 26: "Howto & Style",
              27: "Education", 28: "Science & Technology", 29: "Nonprofits & Activism"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
COLUMNS = ["video_id", "categoryId", "publishedAt", "view_count", "likes", "dislikes", "comment_count"]


def load(path):
    return pd.read_csv(path, usecols=COLUMNS, low_memory=False)


def peak_per_video(df):
    """One row per video (the row with its highest view count), with derived columns."""
    df = df[df.view_count > 0]
    v = df.sort_values("view_count").groupby("video_id").tail(1).copy()
    v["engagement"] = (v.likes + v.dislikes + v.comment_count) / v.view_count * 100
    v["category"] = v.categoryId.map(CATEGORIES)
    v["published"] = pd.to_datetime(v.publishedAt, utc=True, errors="coerce")
    v["weekday"] = v.published.dt.dayofweek
    v["year"] = v.published.dt.year
    return v


def by_category(v, min_videos=200):
    cat = v.groupby("category").agg(videos=("engagement", "size"),
                                    total_views_billions=("view_count", lambda s: s.sum() / 1e9),
                                    mean_engagement=("engagement", "mean"))
    return cat[cat.videos >= min_videos].sort_values("total_views_billions", ascending=False)


def by_weekday(v):
    day = v.dropna(subset=["weekday"]).groupby("weekday").engagement.mean()
    day.index = [DAYS[int(i)] for i in day.index]
    return day


def best_day_per_year(v):
    """{year: (day name, mean engagement)} for the best publish day in each year."""
    out = {}
    for year, g in v.dropna(subset=["year"]).groupby("year"):
        d = g.groupby("weekday").engagement.mean()
        out[int(year)] = (DAYS[int(d.idxmax())], d.max())
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description="Reproduce the headline findings from the raw US file.")
    p.add_argument("path", nargs="?", default="data/US_youtube_trending_data.csv")
    p.add_argument("--min-videos", type=int, default=200,
                   help="hide categories with fewer videos than this (default 200)")
    args = p.parse_args(argv)

    df = load(args.path)
    print(f"{len(df):,} rows, {df.video_id.nunique():,} unique videos")
    v = peak_per_video(df)

    print("\nCategories ranked by total views (billions) and mean engagement rate (%):")
    print(by_category(v, args.min_videos).round(2).to_string())

    print("\nMean engagement rate (%) by publish day (UTC):")
    print(by_weekday(v).round(2).to_string())

    print("\nBest publish day, per year:")
    for year, (day, rate) in best_day_per_year(v).items():
        print(f"  {year}: {day} ({rate:.2f}%)")


if __name__ == "__main__":
    sys.exit(main())
