import numpy as np
import pandas as pd
import pytest

import trending
from conftest import load_script

compare = load_script("compare_countries.py")
sample = load_script("make_sample_data.py")


def test_popularity_tier_boundaries():
    views = pd.Series([0, 99_999, 100_000, 999_999, 1_000_000, 9_999_999, 10_000_000])
    assert list(trending.popularity_tier(views)) == ["Low", "Low", "Medium", "Medium", "High",
                                                     "High", "Viral"]


def test_unknown_category_is_labelled_not_dropped():
    df = pd.DataFrame({"video_id": ["a"], "categoryId": [99], "publishedAt": ["2021-01-01T00:00:00Z"],
                       "view_count": [10], "likes": [1], "dislikes": [0], "comment_count": [0]})
    assert trending.peak_per_video(df).category.iloc[0] == "Category 99"


def test_weekday_hour_and_views_over_time():
    df = pd.DataFrame({
        "video_id": ["a", "a", "b"],
        "categoryId": [10, 10, 23],
        "publishedAt": ["2021-01-01T10:00:00Z", "2021-01-01T10:00:00Z", "2021-01-04T22:30:00Z"],
        "trending_date": ["2021-01-04T00:00:00Z", "2021-01-05T00:00:00Z", "2021-01-10T00:00:00Z"],
        "view_count": [100, 200, 50], "likes": [10, 20, 5], "dislikes": [0, 0, 0],
        "comment_count": [0, 0, 0]})
    v = trending.peak_per_video(df)
    heat = trending.weekday_hour(v).set_index(["day", "hour"])
    assert heat.loc[("Fri", 10), "videos"] == 1
    assert heat.loc[("Mon", 22), "mean_engagement"] == pytest.approx(10.0)

    # one complete Mon-Sun week (Jan 4-10), every trending row's views summed
    assert list(trending.views_over_time(df, "W").views) == [350]
    # a partial week at the end is dropped
    extra = pd.concat([df, df.iloc[[2]].assign(trending_date="2021-01-12T00:00:00Z")])
    assert list(trending.views_over_time(extra, "W").views) == [350]


def test_find_country_files(tmp_path):
    for name in ["US_youtube_trending_data.csv", "GB_youtube_trending_data.csv",
                 "notes.csv", "usa_youtube_trending_data.csv"]:
        (tmp_path / name).write_text("x\n")
    assert sorted(trending.find_country_files(tmp_path)) == ["GB", "US"]


def test_load_reports_missing_columns(tmp_path):
    path = tmp_path / "US_youtube_trending_data.csv"
    pd.DataFrame({"video_id": ["a"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="missing columns"):
        trending.load(path)


def test_compare_countries_end_to_end(tmp_path, capsys):
    rng = np.random.default_rng(0)
    for code in ("US", "GB"):
        sample.make_country(code, 120, rng).to_csv(tmp_path / f"{code}_youtube_trending_data.csv",
                                                   index=False)
    per_country = compare.load_countries(tmp_path, ["US", "GB"])
    table = compare.compare(per_country)
    assert list(table.index) == ["US", "GB"]
    assert (table.videos == 120).all()

    compare.main([str(tmp_path), "--min-videos", "1"])
    out = capsys.readouterr().out
    assert "United Kingdom" in out and "Mean engagement rate (%) by category" in out

    with pytest.raises(SystemExit, match="No file for IN"):
        compare.load_countries(tmp_path, ["IN"])
