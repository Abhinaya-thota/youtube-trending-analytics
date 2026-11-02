"""
Builds the compact copy of the real data that the online dashboard reads, since the raw Kaggle
files are too big for GitHub. For each <CC>_youtube_trending_data.csv it writes:

  online_data/<CC>_videos.parquet   one row per video (its peak-views day), raw columns
  online_data/<CC>_weekly.parquet   views per video per complete trending week

The dashboard computes exactly the same numbers from these as from the raw files.

Usage:  python make_online_data.py [data_dir] [--out-dir online_data]
"""
import argparse
import sys
from pathlib import Path

import trending

# GitHub's web uploader rejects files over 25 MB
UPLOAD_LIMIT_MB = 25


def build_country(df):
    """(videos, weekly) compact tables from one country's raw rows."""
    videos = trending.peak_per_video(df)[trending.COMPACT_COLUMNS].reset_index(drop=True)
    weekly = trending.weekly_views_by_video(df)
    return videos, weekly


def main(argv=None):
    p = argparse.ArgumentParser(description="Build the compact data for the online dashboard.")
    p.add_argument("data_dir", nargs="?", default="data")
    p.add_argument("--out-dir", default=trending.COMPACT_DIR)
    args = p.parse_args(argv)

    files = trending.find_country_files(args.data_dir)
    if not files:
        raise SystemExit(f"No <CC>_youtube_trending_data.csv files found in {args.data_dir}")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    for code, path in files.items():
        videos, weekly = build_country(trending.load(path, trending.CORE_COLUMNS + trending.DETAIL_COLUMNS))
        for name, table in (("videos", videos), ("weekly", weekly)):
            target = out / f"{code}_{name}.parquet"
            table.to_parquet(target, index=False, compression="zstd")
            mb = target.stat().st_size / 1e6
            note = f"  <- over {UPLOAD_LIMIT_MB} MB, too big for GitHub's web upload" \
                if mb > UPLOAD_LIMIT_MB else ""
            print(f"{target}: {len(table):,} rows, {mb:.1f} MB{note}")


if __name__ == "__main__":
    sys.exit(main())
