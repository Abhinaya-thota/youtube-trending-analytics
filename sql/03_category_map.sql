-- 03_category_map.sql: lookup from YouTube category id to name (joined in the workbook).

USE SCHEMA YT_DB.YT_SCHEMA;

CREATE OR REPLACE TABLE CATEGORY_MAP (
  CATEGORY_ID    INTEGER,
  CATEGORY_NAME  VARCHAR
);

INSERT INTO CATEGORY_MAP (CATEGORY_ID, CATEGORY_NAME) VALUES
  (1, 'Film & Animation'), (2, 'Autos & Vehicles'), (10, 'Music'), (15, 'Pets & Animals'),
  (17, 'Sports'), (19, 'Travel & Events'), (20, 'Gaming'), (22, 'People & Blogs'),
  (23, 'Comedy'), (24, 'Entertainment'), (25, 'News & Politics'), (26, 'Howto & Style'),
  (27, 'Education'), (28, 'Science & Technology'), (29, 'Nonprofits & Activism'),
  (43, 'Shows'), (44, 'Trailers');
