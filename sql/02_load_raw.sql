-- 02_load_raw.sql: load the raw trending files (one or more countries) into RAW_TRENDING.
--
-- Upload first with SnowSQL from the folder holding the files. Each file name must start with
-- its two-letter country code: the Kaggle names already do (US_youtube_trending_data.csv), and
-- chunks from 01_split_large_csv.py keep it if you pass e.g. --prefix US_part_
--
--   PUT file://data/chunks/*.csv @YT_STAGE AUTO_COMPRESS = TRUE;

USE SCHEMA YT_DB.YT_SCHEMA;

CREATE OR REPLACE TABLE RAW_TRENDING (
  COUNTRY            VARCHAR(2),
  VIDEO_ID           VARCHAR,
  TITLE              VARCHAR,
  PUBLISHED_AT       TIMESTAMP_NTZ,   -- UTC
  CHANNELID          VARCHAR,
  CHANNELTITLE       VARCHAR,
  CATEGORY_ID        INTEGER,
  TRENDING_DATE      TIMESTAMP_NTZ,
  TAGS               VARCHAR,
  VIEWS              NUMBER(38, 0),
  LIKES              NUMBER(38, 0),
  DISLIKES           NUMBER(38, 0),
  COMMENT_COUNT      NUMBER(38, 0),
  THUMBNAIL_LINK     VARCHAR,
  COMMENTS_DISABLED  BOOLEAN,
  RATINGS_DISABLED   BOOLEAN,
  DESCRIPTION        VARCHAR
);

COPY INTO RAW_TRENDING
FROM (
  SELECT LEFT(SPLIT_PART(METADATA$FILENAME, '/', -1), 2),
         $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
  FROM @YT_STAGE
)
PATTERN = '.*[A-Z][A-Z]_.*[.]csv([.]gz)?'
FILE_FORMAT = (FORMAT_NAME = 'YT_CSV')
ON_ERROR = 'ABORT_STATEMENT';

-- Sanity check: rows and videos per country (US should be 268,787 rows / 47,142 videos).
SELECT COUNTRY, COUNT(*) AS ROWS_LOADED, COUNT(DISTINCT VIDEO_ID) AS VIDEOS
FROM RAW_TRENDING
GROUP BY COUNTRY
ORDER BY COUNTRY;
