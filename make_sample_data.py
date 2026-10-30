"""
Generates SYNTHETIC trending files in the same layout as the Kaggle dataset, so the dashboard,
scripts and SQL can be tried without downloading the real data. The numbers are random and
say nothing about real YouTube behaviour.

Usage:  python make_sample_data.py [--out-dir data/sample] [--countries US GB IN] [--videos 1500]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KAGGLE_COLUMNS = ["video_id", "title", "publishedAt", "channelId", "channelTitle", "categoryId",
                  "trending_date", "tags", "view_count", "likes", "dislikes", "comment_count",
                  "thumbnail_link", "comments_disabled", "ratings_disabled", "description"]

# category id: (share of videos, typical engagement %, typical peak views)
CATEGORY_PROFILE = {10: (0.16, 6.5, 3e6), 24: (0.22, 5.0, 1.5e6), 20: (0.18, 5.5, 8e5),
                    17: (0.10, 2.3, 9e5), 23: (0.04, 7.5, 1e6), 22: (0.10, 6.2, 7e5),
                    25: (0.06, 1.9, 6e5), 28: (0.05, 4.5, 8e5), 1: (0.05, 4.0, 1.2e6),
                    26: (0.04, 5.2, 5e5)}
OPENERS = ["Amazing", "Official", "Worst", "My", "Best", "Funny", "Terrible", "New", "Inside",
           "Happy", "Shocking", "Why", "Beautiful", "Sad", "Epic", "Ultimate", "Honest", "Awful"]
SUBJECTS = ["Music Video", "Highlights", "Day in My Life", "Challenge", "Trailer", "Review",
            "Reaction", "Live Stream", "Tutorial", "Interview", "Prank", "Vlog", "Recap"]
ENDINGS = ["", "", "(Official Video)", "| Full Episode", "- I love it", "gone wrong", "#shorts",
           "- what a fail", "- this is awesome", "part 2"]


def make_country(code, n_videos, rng, start="2021-01-01", days=540):
    cats = list(CATEGORY_PROFILE)
    probs = np.array([CATEGORY_PROFILE[c][0] for c in cats])
    start = pd.Timestamp(start, tz="UTC")
    rows = []
    for i in range(n_videos):
        cat = rng.choice(cats, p=probs / probs.sum())
        _, eng, views = CATEGORY_PROFILE[cat]
        published = start + pd.Timedelta(minutes=int(rng.integers(0, days * 24 * 60)))
        friday_boost = 1.12 if published.dayofweek == 4 else 1.0
        peak_views = int(rng.lognormal(np.log(views), 1.0)) + 1000
        engagement = max(0.2, rng.normal(eng * friday_boost, eng * 0.35)) / 100
        title = " ".join(w for w in [rng.choice(OPENERS), rng.choice(SUBJECTS),
                                     rng.choice(ENDINGS)] if w)
        channel = f"Sample Channel {int(rng.integers(1, n_videos // 4 + 2))}"
        n_days = int(rng.integers(1, 8))
        for d in range(n_days):
            frac = (d + 1) / n_days
            v = int(peak_views * frac)
            interactions = v * engagement
            rows.append({
                "video_id": f"{code}{i:06d}",
                "title": title,
                "publishedAt": published.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "channelId": f"UC{channel[-4:].strip():0>6}",
                "channelTitle": channel,
                "categoryId": int(cat),
                "trending_date": (published.normalize() + pd.Timedelta(days=d + 1))
                .strftime("%Y-%m-%dT00:00:00Z"),
                "tags": "sample|synthetic",
                "view_count": v,
                "likes": int(interactions * 0.9),
                "dislikes": int(interactions * 0.01) if published.year < 2022 else 0,
                "comment_count": int(interactions * 0.09),
                "thumbnail_link": f"https://example.com/{code}{i:06d}.jpg",
                "comments_disabled": False,
                "ratings_disabled": False,
                "description": f"{title}\nSynthetic sample row, not real data.",
            })
    return pd.DataFrame(rows, columns=KAGGLE_COLUMNS)


def main(argv=None):
    p = argparse.ArgumentParser(description="Write synthetic Kaggle-style trending files.")
    p.add_argument("--out-dir", default="data/sample")
    p.add_argument("--countries", nargs="+", default=["US", "GB", "IN"])
    p.add_argument("--videos", type=int, default=1500, help="videos per country (default 1500)")
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args(argv)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    for code in args.countries:
        df = make_country(code, args.videos, rng)
        path = out / f"{code}_youtube_trending_data.csv"
        df.to_csv(path, index=False)
        print(f"Wrote {len(df):,} rows ({args.videos:,} videos) to {path}")


if __name__ == "__main__":
    sys.exit(main())
