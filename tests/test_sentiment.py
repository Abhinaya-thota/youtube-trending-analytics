import numpy as np
import pandas as pd
import pytest

import sentiment
from conftest import load_script

analysis = load_script("sentiment_analysis.py")
sample = load_script("make_sample_data.py")


def test_vader_labels_obvious_titles():
    scores = sentiment.compound_scores(["I love this, best day ever!", "Worst fail, terrible and sad",
                                        "Episode 12", None])
    assert list(sentiment.label(scores)) == ["Positive", "Negative", "Neutral", "Neutral"]


def test_keyword_rule_matches_workbook_precedence():
    # the workbook checks "awesome" before "fail"
    out = sentiment.keyword_rule(["AWESOME fail", "epic FAIL", "nothing", None])
    assert list(out) == ["Positive", "Negative", "Neutral", "Neutral"]


def test_by_sentiment_keeps_all_labels():
    v = pd.DataFrame({"title": ["I love it", "great!", "Episode 3"],
                      "engagement": [4.0, 6.0, 2.0], "view_count": [10, 20, 30]})
    table = sentiment.by_sentiment(sentiment.add_sentiment(v))
    assert list(table.index) == sentiment.LABELS
    assert table.loc["Negative", "videos"] == 0
    assert table.loc["Positive", "mean_engagement"] == 5.0
    assert table.share_pct.sum() == pytest.approx(100)


def test_sentiment_analysis_cli(tmp_path, capsys):
    path = tmp_path / "US_youtube_trending_data.csv"
    sample.make_country("US", 100, np.random.default_rng(2)).to_csv(path, index=False)
    analysis.main([str(path)])
    out = capsys.readouterr().out
    assert "100 videos scored" in out and "Old keyword rule" in out
