"""
Interactive dashboard for the trending analysis: a Python alternative to the Tableau workbook
that reads the raw Kaggle files directly (no Snowflake connection needed).

Usage:  streamlit run app.py
        (put <CC>_youtube_trending_data.csv files in data/, or run make_sample_data.py first)
"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import trending
from sentiment import LABELS, add_sentiment, by_sentiment

BLUE = "#2a78d6"
SEQUENTIAL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
# diverging: negative red, neutral gray midpoint, positive blue
SENTIMENT_COLORS = {"Negative": "#e34948", "Neutral": "#a3a29b", "Positive": "#2a78d6"}
CHART_HEIGHT = 380

st.set_page_config(page_title="YouTube Trending Analytics", page_icon="📈", layout="wide")


@st.cache_data(show_spinner="Loading trending data...")
def load_country(path, code):
    df = trending.load(path, trending.CORE_COLUMNS + trending.DETAIL_COLUMNS, country=code)
    return df, trending.peak_per_video(df)


@st.cache_data(show_spinner="Scoring title sentiment...")
def with_sentiment(v):
    return add_sentiment(v, "title")


def bar(data, x, y, x_title, y_title, tooltip, sort="-x"):
    return (alt.Chart(data)
            .mark_bar(color=BLUE, cornerRadiusEnd=4, height={"band": 0.7})
            .encode(x=alt.X(x, title=x_title), y=alt.Y(y, title=y_title, sort=sort),
                    tooltip=tooltip)
            .properties(height=CHART_HEIGHT))


# ---------- data source ----------
st.sidebar.header("Data")
data_dir = st.sidebar.text_input("Data folder", "data",
                                 help="Folder with Kaggle files named <CC>_youtube_trending_data.csv")
files = trending.find_country_files(data_dir)
using_sample = False
if not files and Path("data/sample").is_dir():
    files = trending.find_country_files("data/sample")
    using_sample = bool(files)

st.title("YouTube Trending Analytics")
if not files:
    st.error(f"No `<CC>_youtube_trending_data.csv` files found in `{data_dir}`. Download the "
             "[Kaggle dataset](https://www.kaggle.com/datasets/rsrishav/youtube-trending-video-dataset)"
             " into `data/`, or run `python make_sample_data.py` to try the dashboard on synthetic data.")
    st.stop()
if using_sample:
    st.warning("Showing **synthetic sample data** from `data/sample` (made by make_sample_data.py). "
               "The numbers are random; add the real Kaggle files to `data/` for real results.")

codes = list(files)
country = st.sidebar.selectbox("Country", codes, index=codes.index("US") if "US" in codes else 0,
                               format_func=lambda c: f"{c} - {trending.COUNTRY_NAMES.get(c, c)}")
raw, videos = load_country(str(files[country]), country)

# ---------- filters ----------
st.sidebar.header("Filters")
dates = videos.published.dropna().dt.date
start, end = st.sidebar.slider("Published between", min_value=dates.min(), max_value=dates.max(),
                               value=(dates.min(), dates.max()), format="YYYY-MM-DD")
categories = sorted(videos.category.unique())
picked = st.sidebar.multiselect("Categories", categories, default=categories)
min_videos = st.sidebar.number_input("Hide categories with fewer videos than", 1, 10_000, 30)

mask = videos.published.dt.date.between(start, end) & videos.category.isin(picked)
v = videos[mask]
raw_f = raw[raw.video_id.isin(v.video_id)]
if v.empty:
    st.info("No videos match these filters.")
    st.stop()

# ---------- headline numbers ----------
day = trending.by_weekday(v)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Trending videos", f"{len(v):,}")
k2.metric("Total views (peak)", f"{v.view_count.sum() / 1e9:.2f}B")
k3.metric("Mean engagement rate", f"{v.engagement.mean():.2f}%")
k4.metric("Best publish day (UTC)", day.idxmax(), f"{day.max() - day.mean():+.2f} pts vs average")

tabs = st.tabs(["Categories", "Publish timing", "Views over time", "Top videos", "Sentiment",
                "Countries"])

# ---------- categories ----------
with tabs[0]:
    cat = trending.by_category(v, min_videos).reset_index()
    if cat.empty:
        st.info("No category has enough videos; lower the minimum in the sidebar.")
    else:
        left, right = st.columns(2)
        left.subheader("Total views")
        left.altair_chart(bar(cat, "total_views_billions:Q", "category:N", "Views (billions)", None,
                              [alt.Tooltip("category:N", title="Category"),
                               alt.Tooltip("total_views_billions:Q", title="Views (B)", format=".2f"),
                               alt.Tooltip("videos:Q", title="Videos", format=",")]),
                          use_container_width=True)
        right.subheader("Engagement rate")
        right.altair_chart(bar(cat, "mean_engagement:Q", "category:N", "Mean engagement (%)", None,
                               [alt.Tooltip("category:N", title="Category"),
                                alt.Tooltip("mean_engagement:Q", title="Engagement (%)", format=".2f"),
                                alt.Tooltip("videos:Q", title="Videos", format=",")]),
                           use_container_width=True)
        st.caption("Engagement rate = (likes + dislikes + comments) / views × 100, using each "
                   "video's peak-views day. Most-viewed categories are not the most engaging.")

# ---------- publish timing ----------
with tabs[1]:
    left, right = st.columns([2, 3])
    day_df = day.rename("mean_engagement").rename_axis("day").reset_index()
    left.subheader("By weekday")
    left.altair_chart(bar(day_df, "mean_engagement:Q", "day:N", "Mean engagement (%)", None,
                          [alt.Tooltip("day:N", title="Day"),
                           alt.Tooltip("mean_engagement:Q", title="Engagement (%)", format=".2f")],
                          sort=trending.DAYS),
                      use_container_width=True)
    right.subheader("By weekday and hour (UTC)")
    heat = trending.weekday_hour(v)
    right.altair_chart(
        alt.Chart(heat).mark_rect(cornerRadius=2, stroke="white", strokeWidth=1)
        .encode(x=alt.X("hour:O", title="Publish hour (UTC)"),
                y=alt.Y("day:N", title=None, sort=trending.DAYS),
                color=alt.Color("mean_engagement:Q", title="Engagement (%)",
                                scale=alt.Scale(range=SEQUENTIAL)),
                tooltip=[alt.Tooltip("day:N", title="Day"), alt.Tooltip("hour:O", title="Hour"),
                         alt.Tooltip("mean_engagement:Q", title="Engagement (%)", format=".2f"),
                         alt.Tooltip("videos:Q", title="Videos", format=",")])
        .properties(height=CHART_HEIGHT),
        use_container_width=True)
    st.caption("Cells with few videos are noisy; hover a cell to see how many videos it averages.")

# ---------- views over time ----------
with tabs[2]:
    st.subheader("Weekly views across trending videos")
    weekly = trending.views_over_time(raw_f, "W")
    hover = alt.selection_point(fields=["date"], nearest=True, on="pointerover", empty=False)
    base = alt.Chart(weekly).encode(x=alt.X("date:T", title="Trending week"))
    line = base.mark_line(color=BLUE, strokeWidth=2).encode(
        y=alt.Y("views:Q", title="Views", axis=alt.Axis(format="~s")))
    points = base.mark_point(color=BLUE, size=60, filled=True).encode(
        y="views:Q",
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
        tooltip=[alt.Tooltip("date:T", title="Week of"),
                 alt.Tooltip("views:Q", title="Views", format=",")]).add_params(hover)
    rule = base.mark_rule(color="gray").encode(
        opacity=alt.condition(hover, alt.value(0.4), alt.value(0)))
    st.altair_chart((line + rule + points).properties(height=CHART_HEIGHT), use_container_width=True)
    st.caption("Sum of view counts over every daily trending row, so a video counts on each day "
               "it trended.")

# ---------- top videos ----------
with tabs[3]:
    st.subheader("Top 10 most viewed videos")
    top = trending.top_videos(v, 10).rename(columns={
        "title": "Title", "channelTitle": "Channel", "category": "Category",
        "view_count": "Views", "engagement": "Engagement (%)"})
    st.dataframe(top, hide_index=True, use_container_width=True,
                 column_config={"Views": st.column_config.NumberColumn(format="localized"),
                                "Engagement (%)": st.column_config.NumberColumn(format="%.2f")})

# ---------- sentiment ----------
with tabs[4]:
    st.subheader("Engagement by title sentiment")
    if country not in trending.ENGLISH_COUNTRIES:
        st.warning("The sentiment model (VADER) only understands English, so results for this "
                   "country are not meaningful.")
    vs = with_sentiment(v)
    sent = by_sentiment(vs).reset_index()
    sent["sentiment"] = sent.sentiment.astype(str)
    # the y-axis already names each bar, so no separate legend
    color = alt.Color("sentiment:N", legend=None,
                      scale=alt.Scale(domain=LABELS, range=[SENTIMENT_COLORS[s] for s in LABELS]))
    tooltip = [alt.Tooltip("sentiment:N", title="Sentiment"),
               alt.Tooltip("videos:Q", title="Videos", format=","),
               alt.Tooltip("share_pct:Q", title="Share (%)", format=".1f"),
               alt.Tooltip("mean_engagement:Q", title="Engagement (%)", format=".2f")]
    left, right = st.columns(2)
    left.markdown("**Share of videos**")
    left.altair_chart(alt.Chart(sent).mark_bar(cornerRadiusEnd=4)
                      .encode(x=alt.X("share_pct:Q", title="Share of videos (%)"),
                              y=alt.Y("sentiment:N", title=None, sort=LABELS),
                              color=color, tooltip=tooltip)
                      .properties(height=200), use_container_width=True)
    right.markdown("**Mean engagement rate**")
    right.altair_chart(alt.Chart(sent).mark_bar(cornerRadiusEnd=4)
                       .encode(x=alt.X("mean_engagement:Q", title="Mean engagement (%)"),
                               y=alt.Y("sentiment:N", title=None, sort=LABELS),
                               color=color, tooltip=tooltip)
                       .properties(height=200), use_container_width=True)
    st.caption("Titles scored with VADER (compound ≥ 0.05 Positive, ≤ -0.05 Negative). This "
               "replaces the workbook's keyword rule, which labels most videos Neutral.")
    examples = vs.sort_values("sentiment_score")[["title", "sentiment_score", "sentiment"]]
    with st.expander("Most positive and negative titles"):
        st.dataframe(pd.concat([examples.tail(5).iloc[::-1], examples.head(5)]),
                     hide_index=True, use_container_width=True)

# ---------- countries ----------
with tabs[5]:
    if len(files) < 2:
        st.info("Add more `<CC>_youtube_trending_data.csv` files (GB, IN, CA, ...) to the data "
                "folder to compare countries.")
    else:
        st.subheader("Country comparison")
        per_country = {c: load_country(str(p), c)[1] for c, p in files.items()}
        summ = pd.DataFrame({c: trending.summary(x) for c, x in per_country.items()}).T
        summ.index.name = "Country"
        st.dataframe(summ.rename(columns={
            "videos": "Videos", "total_views_billions": "Views (B)",
            "mean_engagement": "Engagement (%)", "top_category_by_views": "Top category (views)",
            "top_category_by_engagement": "Top category (engagement)",
            "best_publish_day": "Best day (UTC)", "viral_share": "Viral share (%)"}),
            use_container_width=True,
            column_config={c: st.column_config.NumberColumn(format="%.2f")
                           for c in ["Views (B)", "Engagement (%)", "Viral share (%)"]})

        st.markdown("**Mean engagement rate by category**")
        grid = pd.concat([trending.by_category(x, min_videos).mean_engagement.rename(c)
                          for c, x in per_country.items()], axis=1)
        grid = grid.rename_axis("category").reset_index().melt(
            "category", var_name="country", value_name="mean_engagement").dropna()
        st.altair_chart(
            alt.Chart(grid).mark_rect(cornerRadius=2, stroke="white", strokeWidth=1)
            .encode(x=alt.X("country:N", title=None, axis=alt.Axis(orient="top", labelAngle=0)),
                    y=alt.Y("category:N", title=None),
                    color=alt.Color("mean_engagement:Q", title="Engagement (%)",
                                    scale=alt.Scale(range=SEQUENTIAL)),
                    tooltip=[alt.Tooltip("country:N", title="Country"),
                             alt.Tooltip("category:N", title="Category"),
                             alt.Tooltip("mean_engagement:Q", title="Engagement (%)", format=".2f")])
            .properties(height=CHART_HEIGHT), use_container_width=True)
