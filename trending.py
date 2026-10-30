"""
Shared loading and metrics for the YouTube trending analysis, used by findings_check.py,
compare_countries.py, sentiment_analysis.py and the Streamlit app.

Conventions (match the Tableau workbook and sql/):
- engagement rate = (likes + dislikes + comments) / views * 100
- "one row per video" = the row with the video's highest view count
- publish day and hour are UTC (from publishedAt)
"""
import re
from pathlib import Path

import pandas as pd

CATEGORIES = {1: "Film & Animation", 2: "Autos & Vehicles", 10: "Music", 15: "Pets & Animals",
              17: "Sports", 19: "Travel & Events", 20: "Gaming", 22: "People & Blogs",
              23: "Comedy", 24: "Entertainment", 25: "News & Politics", 26: "Howto & Style",
              27: "Education", 28: "Science & Technology", 29: "Nonprofits & Activism",
              43: "Shows", 44: "Trailers"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
COUNTRY_NAMES = {"US": "United States", "GB": "United Kingdom", "CA": "Canada", "IN": "India",
                 "DE": "Germany", "FR": "France", "BR": "Brazil", "MX": "Mexico", "JP": "Japan",
                 "KR": "South Korea", "RU": "Russia"}
# countries whose titles are mostly English, where the English-only sentiment model is meaningful
ENGLISH_COUNTRIES = {"US", "GB", "CA"}

CORE_COLUMNS = ["video_id", "categoryId", "publishedAt", "view_count", "likes", "dislikes",
                "comment_count"]
DETAIL_COLUMNS = ["title", "channelTitle", "trending_date"]

# popularity tiers by peak view count; same thresholds as POPULARITY_TIER in sql/04_transform.sql
TIERS = [(10_000_000, "Viral"), (1_000_000, "High"), (100_000, "Medium"), (0, "Low")]

FILE_PATTERN = re.compile(r"^([A-Z]{2})_youtube_trending_data\.csv$")


def find_country_files(data_dir):
    """{country code: path} for every Kaggle-style <CC>_youtube_trending_data.csv in data_dir."""
    files = {}
    for path in sorted(Path(data_dir).glob("*_youtube_trending_data.csv")):
        m = FILE_PATTERN.match(path.name)
        if m:
            files[m.group(1)] = path
    return files


def load(path, columns=CORE_COLUMNS, country=None):
    """Read a raw trending file (only `columns`, plus any that exist from DETAIL_COLUMNS if asked)."""
    df = pd.read_csv(path, usecols=lambda c: c in columns, low_memory=False)
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    if country:
        df["country"] = country
    return df


def popularity_tier(views):
    out = pd.Series("Low", index=views.index)
    for threshold, name in reversed(TIERS[:-1]):
        out[views >= threshold] = name
    return out


def peak_per_video(df):
    """One row per video (the row with its highest view count), with derived columns."""
    df = df[df.view_count > 0]
    v = df.sort_values("view_count").groupby("video_id").tail(1).copy()
    v["engagement"] = (v.likes + v.dislikes + v.comment_count) / v.view_count * 100
    v["category"] = v.categoryId.map(CATEGORIES).fillna("Category " + v.categoryId.astype(str))
    v["published"] = pd.to_datetime(v.publishedAt, utc=True, errors="coerce")
    v["weekday"] = v.published.dt.dayofweek
    v["hour"] = v.published.dt.hour
    v["year"] = v.published.dt.year
    v["tier"] = popularity_tier(v.view_count)
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


def weekday_hour(v):
    """Long table of mean engagement and video count per (weekday, hour) of publishing."""
    g = (v.dropna(subset=["weekday", "hour"])
         .groupby(["weekday", "hour"])
         .agg(videos=("engagement", "size"), mean_engagement=("engagement", "mean"))
         .reset_index())
    g["day"] = g.weekday.astype(int).map(dict(enumerate(DAYS)))
    g["hour"] = g.hour.astype(int)
    return g


def best_day_per_year(v):
    """{year: (day name, mean engagement)} for the best publish day in each year."""
    out = {}
    for year, g in v.dropna(subset=["year"]).groupby("year"):
        d = g.groupby("weekday").engagement.mean()
        out[int(year)] = (DAYS[int(d.idxmax())], d.max())
    return out


def views_over_time(df, freq="W"):
    """Total views across all trending rows, per trending period (daily rows summed by `freq`).
    Periods only partly covered by the data (usually the first and last) are dropped, so the
    line doesn't dip at the edges."""
    d = df.assign(date=pd.to_datetime(df.trending_date, utc=True, errors="coerce").dt.tz_localize(None))
    d = d.dropna(subset=["date"])
    out = d.set_index("date").view_count.resample(freq).sum().rename("views").reset_index()
    periods = out.date.dt.to_period(freq)
    complete = (periods.dt.start_time >= d.date.min().normalize()) & \
               (periods.dt.end_time.dt.normalize() <= d.date.max())
    return out[complete].reset_index(drop=True)


def top_videos(v, n=10):
    cols = [c for c in ["title", "channelTitle", "category", "view_count", "engagement"] if c in v]
    return v.nlargest(n, "view_count")[cols].reset_index(drop=True)


def summary(v):
    """Headline numbers for one country (or any subset) of per-video rows."""
    cat = by_category(v, min_videos=1)
    eng = v.groupby("category").engagement.mean()
    day = by_weekday(v)
    return {
        "videos": len(v),
        "total_views_billions": v.view_count.sum() / 1e9,
        "mean_engagement": v.engagement.mean(),
        "top_category_by_views": cat.index[0] if len(cat) else None,
        "top_category_by_engagement": eng.idxmax() if len(eng) else None,
        "best_publish_day": day.idxmax() if len(day) else None,
        "viral_share": (v.tier == "Viral").mean() * 100,
    }
