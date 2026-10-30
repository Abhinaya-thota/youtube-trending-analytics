"""
Cleans the OLDER (2017-18) US trending dataset, "USvideos.csv" (columns: views, publish_time, ...),
for loading into Snowflake. Earlier iteration of the project; the final dashboard uses the newer
US_youtube_trending_data.csv.

Usage:  python 03_clean_older_us_dataset.py [data/USvideos.csv] [-o data/clean_USvideos.csv]
"""
import argparse
import sys

import pandas as pd


def clean(df):
    df = df.copy()
    df["country"] = "US"
    df["publish_time"] = pd.to_datetime(df["publish_time"], errors="coerce")

    # remove rows missing required fields
    df = df.dropna(subset=["video_id", "title", "views"])

    # clean text fields: flatten newlines, trim, and drop non-ASCII (emojis etc.)
    df["description"] = df["description"].fillna("")
    for col in ("title", "description"):
        df[col] = (df[col].str.replace(r"\n", " ", regex=True)
                   .str.encode("ascii", "ignore").str.decode("ascii").str.strip())
    return df


def main(argv=None):
    p = argparse.ArgumentParser(description="Clean the older 2017-18 US trending dataset.")
    p.add_argument("input", nargs="?", default="data/USvideos.csv")
    p.add_argument("-o", "--output", default="data/clean_USvideos.csv")
    args = p.parse_args(argv)

    df = clean(pd.read_csv(args.input))
    df.to_csv(args.output, index=False)
    print(f"Preprocessing complete: {len(df):,} rows saved to {args.output}")


if __name__ == "__main__":
    sys.exit(main())
