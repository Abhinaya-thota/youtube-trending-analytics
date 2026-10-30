"""
Splits a large CSV into chunks under a size limit, repeating the header in each chunk,
so the file can be uploaded to Snowflake.

Usage:  python 01_split_large_csv.py [input.csv] [--max-mb 200] [--prefix US_part_] [--out-dir .]

Start the prefix with the country code (e.g. US_part_): sql/02_load_raw.sql reads the country
from the first two letters of each file name.

Records are parsed with the csv module rather than read line by line: the trending data has
video descriptions containing newlines inside quoted fields, and a naive line split can cut
one record across two files.
"""
import argparse
import csv
import io
import sys
from pathlib import Path


def split_csv(input_file, max_size_mb=200, prefix="part_", out_dir="."):
    """Split input_file into <prefix>N.csv files of at most max_size_mb each. Returns the paths."""
    max_bytes = int(max_size_mb * 1024 * 1024)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def encode_row(row):
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\n").writerow(row)
        return buf.getvalue().encode("utf-8")

    paths = []
    out = None
    current_size = 0

    def open_next():
        nonlocal out, current_size
        if out:
            out.close()
        path = out_dir / f"{prefix}{len(paths) + 1}.csv"
        paths.append(path)
        out = open(path, "wb")
        out.write(header_bytes)
        current_size = len(header_bytes)

    with open(input_file, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header_bytes = encode_row(next(reader))
        open_next()
        for row in reader:
            data = encode_row(row)
            # start a new file if this record would push us over, unless the file is still empty
            if current_size + len(data) > max_bytes and current_size > len(header_bytes):
                open_next()
            out.write(data)
            current_size += len(data)
    out.close()
    return paths


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("input", nargs="?", default="US_youtube_trending_data.csv")
    p.add_argument("--max-mb", type=float, default=200, help="max size per chunk in MB (default 200)")
    p.add_argument("--prefix", default="part_", help="output file prefix (default part_)")
    p.add_argument("--out-dir", default=".", help="output directory (default: current directory)")
    args = p.parse_args(argv)

    paths = split_csv(args.input, args.max_mb, args.prefix, args.out_dir)
    print(f"Split complete: {len(paths)} files created.")
    for path in paths:
        print(f"  {path}")


if __name__ == "__main__":
    sys.exit(main())
