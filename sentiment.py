"""
Title sentiment with VADER, a lexicon/rule-based model built for short social-media text.
Replaces the workbook's keyword rule ("awesome" -> Positive, "fail" -> Negative) as the
main sentiment signal. VADER is English-only, so results for non-English countries are not
meaningful (see trending.ENGLISH_COUNTRIES).
"""
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

LABELS = ["Negative", "Neutral", "Positive"]
# VADER's recommended cut-offs on the compound score
THRESHOLD = 0.05

_analyzer = None


def compound_scores(texts):
    """VADER compound score in [-1, 1] for each text (missing text scores 0)."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    texts = pd.Series(texts).fillna("").astype(str)
    return texts.map(lambda t: _analyzer.polarity_scores(t)["compound"]).astype(float)


def label(compound):
    compound = pd.Series(compound)
    out = pd.Series("Neutral", index=compound.index)
    out[compound >= THRESHOLD] = "Positive"
    out[compound <= -THRESHOLD] = "Negative"
    return pd.Categorical(out, categories=LABELS, ordered=True)


def keyword_rule(descriptions):
    """The Tableau workbook's original rule on the description, for comparison."""
    d = pd.Series(descriptions).fillna("").str.lower()
    out = pd.Series("Neutral", index=d.index)
    out[d.str.contains("fail", regex=False)] = "Negative"
    out[d.str.contains("awesome", regex=False)] = "Positive"  # checked first in the workbook
    return pd.Categorical(out, categories=LABELS, ordered=True)


def add_sentiment(v, text_column="title"):
    """Adds sentiment_score and sentiment columns to per-video rows."""
    v = v.copy()
    v["sentiment_score"] = compound_scores(v[text_column]).values
    v["sentiment"] = label(v["sentiment_score"]).astype(str)
    v["sentiment"] = pd.Categorical(v["sentiment"], categories=LABELS, ordered=True)
    return v


def by_sentiment(v):
    return (v.groupby("sentiment", observed=False)
            .agg(videos=("engagement", "size"),
                 share_pct=("engagement", lambda s: len(s) / len(v) * 100),
                 mean_engagement=("engagement", "mean"),
                 median_views=("view_count", "median")))
