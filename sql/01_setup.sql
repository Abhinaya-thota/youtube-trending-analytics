-- 01_setup.sql: warehouse, database, schema, file format and stage.
-- Names match the Tableau workbook's connection (YT_WH / YT_DB / YT_SCHEMA).
-- Reconstructed from the workbook's schema; the original load scripts were not kept.

CREATE WAREHOUSE IF NOT EXISTS YT_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
CREATE DATABASE IF NOT EXISTS YT_DB;
CREATE SCHEMA IF NOT EXISTS YT_DB.YT_SCHEMA;

USE WAREHOUSE YT_WH;
USE SCHEMA YT_DB.YT_SCHEMA;

-- The Kaggle CSVs have quoted fields with embedded newlines (descriptions) and ISO timestamps
-- such as 2021-01-01T10:00:00Z, which are UTC.
CREATE OR REPLACE FILE FORMAT YT_CSV
  TYPE = CSV
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('')
  EMPTY_FIELD_AS_NULL = TRUE
  TIMESTAMP_FORMAT = 'YYYY-MM-DD"T"HH24:MI:SS"Z"'
  ENCODING = 'UTF8';

CREATE OR REPLACE STAGE YT_STAGE FILE_FORMAT = YT_CSV;
