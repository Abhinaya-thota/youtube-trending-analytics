import pandas as pd
import pytest

import findings_check as fc
import trending
from conftest import load_script

clean_older = load_script("03_clean_older_us_dataset.py")


@pytest.fixture
def raw():
    # v1 trends twice (peak row is the second); v2 is Comedy; v3 has zero views and is dropped
    return pd.DataFrame({
        "video_id": ["v1", "v1", "v2", "v3"],
        "categoryId": [10, 10, 23, 24],
        "publishedAt": ["2021-01-01T10:00:00Z"] * 2 + ["2021-01-04T10:00:00Z", "2022-01-07T00:00:00Z"],
        "view_count": [100, 1000, 200, 0],
        "likes": [5, 50, 20, 0],
        "dislikes": [0, 0, 0, 0],
        "comment_count": [5, 10, 10, 0],
    })


def test_peak_per_video(raw):
    v = trending.peak_per_video(raw).set_index("video_id")
    assert list(v.index.sort_values()) == ["v1", "v2"]
    assert v.loc["v1", "view_count"] == 1000
    assert v.loc["v1", "engagement"] == pytest.approx(6.0)  # (50 + 0 + 10) / 1000 * 100
    assert v.loc["v2", "engagement"] == pytest.approx(15.0)
    assert v.loc["v1", "category"] == "Music"
    assert v.loc["v1", "weekday"] == 4  # 2021-01-01 was a Friday


def test_aggregations(raw):
    v = trending.peak_per_video(raw)
    cat = trending.by_category(v, min_videos=1)
    assert list(cat.index) == ["Music", "Comedy"]  # ranked by total views
    assert trending.by_category(v, min_videos=2).empty

    day = trending.by_weekday(v)
    assert day["Fri"] == pytest.approx(6.0)
    assert day["Mon"] == pytest.approx(15.0)
    assert trending.best_day_per_year(v) == {2021: ("Mon", pytest.approx(15.0))}


def test_main_runs_end_to_end(raw, tmp_path, capsys):
    path = tmp_path / "us.csv"
    raw.to_csv(path, index=False)
    fc.main([str(path), "--min-videos", "1"])
    out = capsys.readouterr().out
    assert "4 rows, 3 unique videos" in out
    assert "2021: Mon" in out


def test_clean_older_dataset():
    df = pd.DataFrame({
        "video_id": ["a", "b", None],
        "title": [" Hello\nworld 🎉 ", "t", "x"],
        "description": [None, "line\nbreak", "d"],
        "views": [1, 2, 3],
        "publish_time": ["2017-11-13T17:13:01.000Z", "not a date", "2017-11-13T17:13:01.000Z"],
    })
    out = clean_older.clean(df)
    assert list(out.video_id) == ["a", "b"]
    assert out.title.iloc[0] == "Hello world"
    assert list(out.description) == ["", "line break"]
    assert (out.country == "US").all()
    assert pd.isna(out.publish_time.iloc[1])
