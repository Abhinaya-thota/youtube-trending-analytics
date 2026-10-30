# YouTube Trending Video Analytics (US)

An analysis of what separates YouTube's trending videos in the US: which categories draw the most views, which ones draw the most engagement, and whether publish timing matters. The data was prepared in Python, loaded into Snowflake, and explored in Tableau.

## Data

[YouTube Trending Video Dataset](https://www.kaggle.com/datasets/rsrishav/youtube-trending-video-dataset) (Kaggle), US file: **268,787 daily trending records covering 47,142 unique videos**, published between August 2020 and April 2024. The data is not included in this repo (the raw file is about 400MB). An earlier iteration of the project used the older [2017-18 trending dataset](https://www.kaggle.com/datasets/datasnaek/youtube-new).

## Workflow

1. **Prepare:** split the large raw CSV into chunks under 200MB so it could be uploaded (`01_split_large_csv.py`), and check column schemas (`02_list_columns.py`).
2. **Load and model:** load the data into **Snowflake** and join it to a category lookup table, giving the table the workbook reads (`US_YOUTUBE_VIDEOSFINAL` plus `CATEGORY_MAP`).
3. **Visualize:** build four Tableau worksheets in `youtube_trending_dashboard.twb`:
   - Engagement by Category
   - Publish Time vs Engagement
   - Views over Time
   - Top 10 Most Viewed Videos

Metrics defined in the workbook:
- **Engagement rate** = (likes + dislikes + comments) / views x 100
- **Sentiment** = a simple keyword rule on the video description ("awesome" gives Positive, "fail" gives Negative, otherwise Neutral)

## Key Findings

Computed with `findings_check.py` from the raw US file, using one row per video (its peak view count) and the engagement definition above.

- **Views and engagement don't line up.** Music and Entertainment lead in total views (36.1B and 33.0B). Comedy ranks only 8th in views but **first in engagement (7.6%)**, followed by Music (6.6%) and People & Blogs (6.3%). Entertainment, #2 in views, sits mid-pack at 5.1%. Sports (2.2%) and News & Politics (1.8%) are the least engaging categories.
- **Friday uploads had the highest engagement.** Average engagement for videos published on a Friday was 5.6%, against 4.8% to 5.2% on every other day, and Friday ranked first in **every year from 2020 to 2024**. Weekend uploads were slightly lower than weekdays (4.9% vs 5.2%).

## Reproducing the numbers

```bash
pip install -r requirements.txt
python findings_check.py data/US_youtube_trending_data.csv
```

## Limitations

- **US only.** Trending behavior in other countries may differ.
- **Dislike counts are mostly zero.** About 36% of rows have a non-zero dislike count, which fits YouTube hiding public dislikes in late 2021. Engagement rate is almost unchanged if dislikes are left out, and the findings above hold either way.
- **Sentiment is a crude keyword rule**, not a trained sentiment model, so it should be treated as a rough signal only.
- **Publish day and hour are in UTC** (from the dataset's `publishedAt` field), not the uploader's local time.
- The workbook's data connection points at Snowflake, and the account details have been replaced with placeholders. Tableau will ask you to reconnect to your own data source, and the worksheets will only render once you do.
- The Snowflake load and SQL transformations are not included in this repo.

## Repository Structure

```
├── 01_split_large_csv.py                # Splits a large CSV into <200MB chunks
├── 02_list_columns.py                   # Prints a CSV's column headers
├── 03_clean_older_us_dataset.py         # Cleaning for the older (2017-18) US dataset
├── findings_check.py                    # Reproduces the headline numbers in pandas
├── youtube_trending_dashboard.twb       # Tableau workbook (4 worksheets)
└── requirements.txt
```

## Tech Stack

`Python (pandas)` `Snowflake` `SQL` `Tableau`
