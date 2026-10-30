"""
Compares the headline findings across countries, for every Kaggle file named
<CC>_youtube_trending_data.csv in a folder (US, GB, IN, ...).

Usage:  python compare_countries.py [data_dir] [--countries US GB IN]
"""
import argparse
import sys

import pandas as pd

from trending import COUNTRY_NAMES, by_category, find_country_files, load, peak_per_video, summary


def load_countries(data_dir, countries=None):
    """{code: per-video rows} for the requested (or all found) countries."""
    files = find_country_files(data_dir)
    if countries:
        missing = [c for c in countries if c not in files]
        if missing:
            raise SystemExit(f"No file for {', '.join(missing)} in {data_dir}; found {sorted(files)}")
        files = {c: files[c] for c in countries}
    if not files:
        raise SystemExit(f"No <CC>_youtube_trending_data.csv files found in {data_dir}")
    return {code: peak_per_video(load(path, country=code)) for code, path in files.items()}


def compare(per_country):
    rows = {code: summary(v) for code, v in per_country.items()}
    table = pd.DataFrame(rows).T
    table.index.name = "country"
    return table


def category_engagement(per_country, min_videos=50):
    """Mean engagement per category (rows) and country (columns)."""
    cols = {code: by_category(v, min_videos).mean_engagement for code, v in per_country.items()}
    return pd.DataFrame(cols).sort_index()


def main(argv=None):
    p = argparse.ArgumentParser(description="Compare trending findings across countries.")
    p.add_argument("data_dir", nargs="?", default="data")
    p.add_argument("--countries", nargs="+", help="country codes, e.g. US GB IN (default: all found)")
    p.add_argument("--min-videos", type=int, default=50,
                   help="hide categories with fewer videos than this in a country (default 50)")
    args = p.parse_args(argv)

    per_country = load_countries(args.data_dir, args.countries)
    print("Countries: " + ", ".join(f"{c} ({COUNTRY_NAMES.get(c, c)})" for c in per_country))

    print("\nHeadline numbers per country:")
    with pd.option_context("display.float_format", "{:.2f}".format, "display.width", 200):
        print(compare(per_country).to_string())

    print("\nMean engagement rate (%) by category and country:")
    print(category_engagement(per_country, args.min_videos).round(2).to_string())


if __name__ == "__main__":
    sys.exit(main())
