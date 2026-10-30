"""
Runs the Snowflake SQL in sql/ against DuckDB (transpiled with sqlglot) on synthetic data, and
checks the results match the pandas pipeline in trending.py. This catches logic drift between
the two; it can't catch Snowflake-only issues such as the PUT/COPY load in 02_load_raw.sql.
"""
from pathlib import Path

import duckdb
import pandas as pd
import pytest
import sqlglot

import trending
from conftest import ROOT, load_script

SQL = ROOT / "sql"
sample = load_script("make_sample_data.py")


def statements(path, dialect="duckdb"):
    """Snowflake statements from a file, transpiled, minus USE (no warehouse/schema in DuckDB)."""
    out = []
    for stmt in sqlglot.parse(Path(path).read_text(), read="snowflake"):
        if stmt is None or stmt.key == "use":
            continue
        out.append(stmt.sql(dialect=dialect))
    return out


@pytest.fixture(scope="module")
def raw():
    rng = __import__("numpy").random.default_rng(1)
    return pd.concat([sample.make_country(c, 400, rng).assign(country=c) for c in ("US", "GB")],
                     ignore_index=True)


@pytest.fixture(scope="module")
def con(raw):
    con = duckdb.connect()
    r = raw.rename(columns={"view_count": "VIEWS", "categoryId": "CATEGORY_ID",
                            "publishedAt": "PUBLISHED_AT", "trending_date": "TRENDING_DATE"})
    r.columns = [c.upper() for c in r.columns]
    for col in ("PUBLISHED_AT", "TRENDING_DATE"):
        r[col] = pd.to_datetime(r[col], utc=True).dt.tz_localize(None)  # TIMESTAMP_NTZ, UTC
    con.register("raw_df", r)
    con.execute("CREATE TABLE RAW_TRENDING AS SELECT * FROM raw_df")
    for f in ("03_category_map.sql", "04_transform.sql"):
        for s in statements(SQL / f):
            con.execute(s)
    return con


def test_every_file_parses_as_snowflake():
    for path in sorted(SQL.glob("*.sql")):
        assert sqlglot.parse(path.read_text(), read="snowflake"), path


def test_final_table_has_the_workbook_columns(con):
    cols = [r[0] for r in con.execute("DESCRIBE US_YOUTUBE_VIDEOSFINAL").fetchall()]
    workbook = {"VIDEO_ID", "TITLE", "PUBLISHED_AT", "CHANNELID", "CHANNELTITLE", "CATEGORY_ID",
                "TRENDING_DATE", "TAGS", "VIEWS", "LIKES", "DISLIKES", "COMMENT_COUNT",
                "THUMBNAIL_LINK", "COMMENTS_DISABLED", "RATINGS_DISABLED", "DESCRIPTION",
                "PUBLISH_HOUR", "LIKES_TO_VIEWS_RATIO", "POPULARITY_TIER", "SENTIMENT"}
    assert set(cols) == workbook
    countries = con.execute("SELECT DISTINCT COUNTRY FROM YOUTUBE_VIDEOS_ALL").fetchall()
    assert sorted(c[0] for c in countries) == ["GB", "US"]


def test_category_map_matches_python(con):
    rows = dict(con.execute("SELECT CATEGORY_ID, CATEGORY_NAME FROM CATEGORY_MAP").fetchall())
    assert rows == trending.CATEGORIES


def test_analysis_queries_match_pandas(con, raw):
    queries = statements(SQL / "05_analysis.sql")
    category_sql, weekday_sql, _heatmap_sql, country_sql, top_sql = queries

    v = trending.peak_per_video(raw[raw.country == "US"])

    # category query has HAVING COUNT(*) >= 200; drop it to compare all categories
    cat = con.execute(category_sql.replace("HAVING COUNT(*) >= 200", "")).df().set_index("CATEGORY_NAME")
    expected = trending.by_category(v, min_videos=1)
    pd.testing.assert_series_equal(cat.MEAN_ENGAGEMENT.sort_index(),
                                   expected.mean_engagement.sort_index(),
                                   check_names=False, check_index_type=False)
    assert dict(cat.VIDEOS.astype(int)) == dict(expected.videos)

    day = con.execute(weekday_sql).df()
    day.index = [trending.DAYS[i - 1] for i in day.PUBLISH_WEEKDAY]
    pd.testing.assert_series_equal(day.MEAN_ENGAGEMENT, trending.by_weekday(v), check_names=False)

    countries = con.execute(country_sql).df().set_index("COUNTRY")
    for code in ("US", "GB"):
        s = trending.summary(trending.peak_per_video(raw[raw.country == code]))
        assert countries.loc[code, "VIDEOS"] == s["videos"]
        assert countries.loc[code, "MEAN_ENGAGEMENT"] == pytest.approx(s["mean_engagement"])
        assert countries.loc[code, "VIRAL_SHARE"] == pytest.approx(s["viral_share"])

    top = con.execute(top_sql).df()
    assert list(top.VIEWS) == list(trending.top_videos(v).view_count)


def test_tiers_and_sentiment_rule_match_python(con, raw):
    df = con.execute("SELECT VIEWS, POPULARITY_TIER, DESCRIPTION, SENTIMENT FROM YOUTUBE_VIDEOS_ALL").df()
    assert list(df.POPULARITY_TIER) == list(trending.popularity_tier(df.VIEWS))
    from sentiment import keyword_rule
    assert list(df.SENTIMENT) == list(keyword_rule(df.DESCRIPTION).astype(str))
