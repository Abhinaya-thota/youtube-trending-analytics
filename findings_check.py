"""
Reproduces the headline numbers from the analysis in pandas, straight from the raw US file,
so the findings can be checked without a Snowflake/Tableau connection.

Usage:  python findings_check.py [path/to/US_youtube_trending_data.csv] [--min-videos 200]

Method: one row per video (its peak view count), engagement rate defined as in the Tableau
workbook: (likes + dislikes + comments) / views * 100. Publish day/hour are UTC (publishedAt).
The calculations live in trending.py.
"""
import argparse
import sys

from trending import best_day_per_year, by_category, by_weekday, load, peak_per_video


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
