"""The compact online_data/ copy must give the dashboard exactly the same numbers as raw files."""
import numpy as np
import pandas as pd

import trending
from conftest import load_script

online = load_script("make_online_data.py")
sample = load_script("make_sample_data.py")


def build(tmp_path, codes=("US", "GB"), n=300):
    rng = np.random.default_rng(5)
    raw_dir, out_dir = tmp_path / "data", tmp_path / "online_data"
    raw_dir.mkdir()
    for code in codes:
        sample.make_country(code, n, rng).to_csv(raw_dir / f"{code}_youtube_trending_data.csv",
                                                 index=False)
    online.main([str(raw_dir), "--out-dir", str(out_dir)])
    return raw_dir, out_dir


def test_compact_files_match_raw(tmp_path):
    raw_dir, out_dir = build(tmp_path)
    compact = trending.find_compact_files(out_dir)
    assert sorted(compact) == ["GB", "US"]

    for code, raw_path in trending.find_country_files(raw_dir).items():
        raw = trending.load(raw_path, trending.CORE_COLUMNS + trending.DETAIL_COLUMNS)
        expected = trending.peak_per_video(raw)
        videos_path, weekly_path = compact[code]
        got = trending.peak_per_video(pd.read_parquet(videos_path))

        assert len(got) == len(expected)
        assert trending.summary(got) == trending.summary(expected)
        pd.testing.assert_frame_equal(trending.by_category(got, 1), trending.by_category(expected, 1))
        pd.testing.assert_series_equal(trending.by_weekday(got), trending.by_weekday(expected))
        pd.testing.assert_frame_equal(trending.top_videos(got).reset_index(drop=True),
                                      trending.top_videos(expected).reset_index(drop=True))

        weekly = pd.read_parquet(weekly_path).groupby("date", as_index=False).views.sum()
        pd.testing.assert_frame_equal(weekly, trending.views_over_time(raw), check_dtype=False)


def test_find_compact_files_needs_both_halves(tmp_path):
    (tmp_path / "US_videos.parquet").write_bytes(b"")
    (tmp_path / "US_weekly.parquet").write_bytes(b"")
    (tmp_path / "GB_videos.parquet").write_bytes(b"")  # no GB_weekly
    assert list(trending.find_compact_files(tmp_path)) == ["US"]
