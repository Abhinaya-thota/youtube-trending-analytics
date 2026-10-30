import csv

from conftest import load_script

split = load_script("01_split_large_csv.py")
columns = load_script("02_list_columns.py")


def write_sample(path, n=200):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["video_id", "title", "description"])
        for i in range(n):
            # embedded newlines and commas inside quoted fields, plus non-ASCII
            w.writerow([f"id{i}", f"Title, {i} 🎵", f"line one\nline two\r\nline {i}"])


def read_rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def test_split_keeps_multiline_records_intact(tmp_path):
    src = tmp_path / "in.csv"
    write_sample(src)
    paths = split.split_csv(src, max_size_mb=0.002, out_dir=tmp_path / "out")  # ~2KB chunks

    assert len(paths) > 1
    original = read_rows(src)
    header, body = original[0], []
    for p in paths:
        rows = read_rows(p)
        assert rows[0] == header
        assert all(len(r) == 3 for r in rows)
        assert p.stat().st_size <= 0.002 * 1024 * 1024
        body.extend(rows[1:])
    assert body == original[1:]


def test_split_single_file_when_under_limit(tmp_path):
    src = tmp_path / "in.csv"
    write_sample(src, n=5)
    paths = split.split_csv(src, max_size_mb=10, out_dir=tmp_path)
    assert len(paths) == 1
    assert read_rows(paths[0]) == read_rows(src)


def test_list_columns_handles_quoted_headers(tmp_path, capsys):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text('id,"title, full",views\n1,x,2\n', encoding="utf-8")
    b.write_text("id,title,views\n", encoding="utf-8")
    assert columns.read_columns(a) == ["id", "title, full", "views"]
    assert columns.main([str(a), str(a)]) == 0
    assert columns.main([str(a), str(b)]) == 1
    assert "WARNING" in capsys.readouterr().out
