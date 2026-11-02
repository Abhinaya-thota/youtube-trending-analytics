"""Smoke test: the Streamlit app renders every tab on synthetic data without errors."""
import shutil

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT, load_script

sample = load_script("make_sample_data.py")


@pytest.fixture
def app_dir(tmp_path, monkeypatch):
    rng = np.random.default_rng(3)
    data = tmp_path / "data"
    data.mkdir()
    for code in ("US", "IN"):
        sample.make_country(code, 150, rng).to_csv(data / f"{code}_youtube_trending_data.csv",
                                                    index=False)
    for f in ("app.py", "trending.py", "sentiment.py"):
        shutil.copy(ROOT / f, tmp_path / f)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_app_renders_with_two_countries(app_dir):
    at = AppTest.from_file(str(app_dir / "app.py"), default_timeout=60).run()
    assert not at.exception
    assert [m.label for m in at.metric][0] == "Trending videos"
    assert len(at.tabs) == 6
    assert not at.warning or "synthetic" not in at.warning[0].value  # real-data folder, no banner

    assert not any("only understands English" in w.value for w in at.warning)

    # India: titles aren't (all) English, so the sentiment tab carries a warning
    at.sidebar.selectbox[0].set_value("IN").run()
    assert not at.exception
    assert any("only understands English" in w.value for w in at.warning)


def test_app_explains_missing_data(tmp_path, monkeypatch):
    shutil.copy(ROOT / "app.py", tmp_path / "app.py")
    for f in ("trending.py", "sentiment.py"):
        shutil.copy(ROOT / f, tmp_path / f)
    monkeypatch.chdir(tmp_path)
    at = AppTest.from_file(str(tmp_path / "app.py"), default_timeout=60).run()
    assert not at.exception
    assert "make_sample_data.py" in at.error[0].value


def test_app_uses_compact_online_data(tmp_path, monkeypatch):
    """Online deployment: no data/ folder, only the compact files in online_data/."""
    online = load_script("make_online_data.py")
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    sample.make_country("US", 150, np.random.default_rng(4)).to_csv(
        raw_dir / "US_youtube_trending_data.csv", index=False)
    online.main([str(raw_dir), "--out-dir", str(tmp_path / "online_data")])
    for f in ("app.py", "trending.py", "sentiment.py"):
        shutil.copy(ROOT / f, tmp_path / f)
    monkeypatch.chdir(tmp_path)

    at = AppTest.from_file(str(tmp_path / "app.py"), default_timeout=60).run()
    assert not at.exception
    assert not at.error
    assert any("compact copy" in c.value for c in at.caption)
    assert not any("synthetic" in w.value for w in at.warning)
    assert at.metric[0].value == "150"
