"""
Prints the column headers of one or more CSV files, e.g. to check that split chunks
share the same schema before loading them into Snowflake.

Usage:  python 02_list_columns.py part_1.csv [part_2.csv ...]
"""
import argparse
import csv
import sys


def read_columns(path):
    with open(path, encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("files", nargs="+", help="CSV file(s) to inspect")
    args = p.parse_args(argv)

    schemas = {}
    for path in args.files:
        columns = read_columns(path)
        schemas[path] = columns
        print(f"Columns in {path} ({len(columns)}):")
        for col in columns:
            print(f"  {col}")

    if len({tuple(c) for c in schemas.values()}) > 1:
        print("\nWARNING: files do not share the same columns.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
