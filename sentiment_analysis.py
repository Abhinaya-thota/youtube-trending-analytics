"""
Scores every trending video's title with VADER and compares engagement across Positive,
Neutral and Negative titles. Also shows how the workbook's old keyword rule (on descriptions)
compares, since that rule labels almost everything Neutral.

Usage:  python sentiment_analysis.py [path/to/US_youtube_trending_data.csv]
"""
import argparse
import sys

import pandas as pd

from sentiment import add_sentiment, by_sentiment, keyword_rule
from trending import CORE_COLUMNS, load, peak_per_video


def main(argv=None):
    p = argparse.ArgumentParser(description="Engagement by title sentiment (VADER).")
    p.add_argument("path", nargs="?", default="data/US_youtube_trending_data.csv")
    args = p.parse_args(argv)

    v = peak_per_video(load(args.path, CORE_COLUMNS + ["title", "description"]))
    v = add_sentiment(v, "title")
    print(f"{len(v):,} videos scored on their title\n")

    print("Title sentiment (VADER) vs engagement:")
    print(by_sentiment(v).round(2).to_string())

    v["keyword_rule"] = keyword_rule(v.description)
    print("\nOld keyword rule on descriptions, share of videos (%):")
    print((v.keyword_rule.value_counts(normalize=True, sort=False) * 100).round(1).to_string())

    print("\nVADER (rows) vs keyword rule (columns), number of videos:")
    print(pd.crosstab(v.sentiment, v.keyword_rule).to_string())

    print("\nMost positive and most negative titles:")
    ranked = v.sort_values("sentiment_score")
    for _, r in pd.concat([ranked.tail(3).iloc[::-1], ranked.head(3)]).iterrows():
        print(f"  {r.sentiment_score:+.2f}  {r.title[:90]}")


if __name__ == "__main__":
    sys.exit(main())
